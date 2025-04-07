import os
import subprocess
import re

class JobStatus():
    def __init__(self,name):
        self.Name = name
        self.Stage = 0
        self.Report = "Initiated Job"
        self.Errors = []
        self.Source = None

    def Progress_report(self):
        print(f"We are on stage {self.Stage} of {self.Name}."
              f"Current report is: {self.Report}")

    def Update_report(self,NewStage,NewReport):
        self.Stage = NewStage
        self.Report = NewReport
        self.Progress_report()
        f = open(report_path, "w")
        f.write(str(NewStage))
        f.close()

    def Stop(self):
        print("\n")*2
        self.Progress_report()
        print(f"Errors during processing were:")
        for e in self.Errors:
            print(e)
        print("\n") * 3

# Create a progress report txt for tracking how far through the process we are.

def ImgtoSplat(scan_path):
    scan_name = os.path.split(scan_path)[:-1]
    scan_name = scan_name
    current_job = JobStatus(scan_name)
    current_job.Progress_report

    threeD_models_path = os.path.abspath(os.path.join(scan_path, "3dmodels"))
    images_path = os.path.abspath(os.path.join(scan_path, "Images"))
    forward_images_path = os.path.abspath(os.path.join(scan_path, "Forward Only"))
    report_path = os.path.join(threeD_models_path,"Report.txt")

    # Work out what was the source of our images based on file names (I should really be adding this to the report.)
    test_name_file = os.listdir(images_path)[0]
    if "stalls" in test_name_file or "gallery" in test_name_file or "seating" in test_name_file or "circle" in test_name_file:
        current_job.Source = "Preevue"
    elif re.match("[0-9a-f]{32}",test_name_file[:-10]):
        current_job.Source = "Matterport"
    else:
        print("Unable to work out image source formatting. Skipping.")
        print(test_name_file)
        return None

    print(current_job.Source)

    rcproj_save_path = os.path.join(threeD_models_path, f"{scan_name}.rcproj")
    psht_save_path = os.path.join(threeD_models_path, f"{scan_name}.psht")
    ply_export_path = os.path.join(images_path,f"{scan_name}.ply")
    csv_export_path = os.path.join(images_path,f"{scan_name}.csv")
    calibration_export_settings_path = r"C:\Users\Ben.Garcia\PycharmProjects\360Images_to_GS\RCcalibration.xml"

    # We check the progress report so that we skip venues already processed.
    try:
        progress = float(open(report_path, "r").read())
    except FileNotFoundError:
        current_job.Update_report(0,"Yet to begin")
        progress = float(open(report_path, "r").read())

    if progress == 4:
        # Skip when we've finished the whole process
        return None
    elif progress > 0:
        current_job.Stage = progress
        current_job.Progress_report



    # Reality Capture command line to align only forward facing images.
    # Export Reality capture result using internal/external camera properties.
    # Export reality capture spare point cloud.
    # TODO: Run a timer for Reality Capture. If it takes longer than 20 minutes, quit out and report an error. Sometimes Reality Capture just freezes on the alignment and I really don't know why. Seems worse with larger datasets.

    if current_job.Source == "Preevue":
        direction_strings_selection = r'-selectImage g/[_f]\./'
        alignment_target = 0.2
    elif current_job.Source == "Matterport":
        alignment_target = 0.3
        direction_strings_selection = r'-selectImage g/[face1]\./ -selectImage g/face2/ union -selectImage g/face3/ union -selectImage g/face4/ union' #

    if current_job.Stage <= 1:
        def RealityCaptureInitialAlignment():
            current_job.Update_report(1, "Starting Reality Capture")

            try:
                # raise FloatingPointError("This is fine & helps skip the RC section for testing")
                subprocess.run([r"Batch_Scripts\RealityCaptureAlignment.bat",
                                scan_name,
                                images_path,
                                rcproj_save_path,
                                ply_export_path,
                                csv_export_path,
                                calibration_export_settings_path,
                                direction_strings_selection], text=True)


            except subprocess.CalledProcessError as e:
                print(f"Command failed with return code {e.returncode}")
            except FloatingPointError:
                pass

        RealityCaptureInitialAlignment()
        current_job.Update_report(1.1, "Completed Reality Capture. Testing alignment")

    if current_job.Stage == 1.2:
        # We had previously paused this job to do manual alignment. Now trying to export again to see if we have improved the alignment.
        try:
            # raise FloatingPointError("This is fine & helps skip the RC section for testing")
            subprocess.run([r"Batch_Scripts\RealityCaptureExport.bat",
                            scan_name,
                            images_path,
                            rcproj_save_path,
                            ply_export_path,
                            csv_export_path,
                            calibration_export_settings_path,
                            direction_strings_selection], text=True)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")

    if 2 > current_job.Stage > 1:
        # We need to test how well the alignment went. If Preevue, expect 1/4 images to be used at best. If Matterport, 2/3 is best but 1/3 is probably acceptable.
        with open(csv_export_path) as f:
            cameras_aligned_count = sum(1 for line in f) -1

        cameras_total_count = len(os.listdir(images_path))
        cameras_aligned_percent = cameras_aligned_count / cameras_total_count
        # print(cameras_aligned_count,cameras_total_count, cameras_aligned_percent)
        if cameras_aligned_percent > alignment_target:
            current_job.Update_report(2, f"Alignment passes target {str(cameras_aligned_percent*100)[:4]}%. Calculating Extra Image Positions")
        else:
            current_job.Update_report(1.2,
                                      f"Alignment does not pass target {str(cameras_aligned_percent * 100)[:4]}%. Pausing for manual alignment.")
            return None

    if 3 > current_job.Stage >= 2:
        #Delete the old csv.
        os.remove(csv_export_path)
        os.remove(os.path.join(images_path,"crmeta.db")) # I don't know what is making these db files but they aren't needed so I'm deleting them.
        current_job.Update_report(3, "Calulated new positions.")

    if 4 > current_job.Stage >= 3:
        current_job.Update_report(3.1, "Starting Postshot")
        # Import Images, CSV, Sparse PLY into Postshot on command line.
        try:
            # raise FloatingPointError("This is fine & helps skip the RC section for testing")
            RC_Command = subprocess.run([r"Batch_Scripts\PostshotSplatting.bat",
                                         images_path,
                                         psht_save_path], text=True)

        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
        except FloatingPointError:
            print("Test err")
            pass

        current_job.Update_report(4, "Completed Postshot. Finishing for now.")


    # Update report txt