import os.path
from os import listdir

from filter_raw_data import main as filter_raw


videos_dir = r"C:\Users\Ben.Garcia\OneDrive - d&b solutions\Desktop\Projects\Scanning Stick\4-4-24 Lobby Scan"
videos = listdir(videos_dir)
sharp_frames_dir = os.path.join(videos_dir,"Sharp Frames")
if not os.path.exists(sharp_frames_dir):
    os.mkdir(sharp_frames_dir)

print(videos)

for file in videos:
    if ".mp4" not in file.lower():
        print("Not an MP4")
        continue
    print(file)

    video_path = os.path.join(videos_dir,file)
    frames_path = os.path.join(sharp_frames_dir,file[:-4]) # We make a dir in the sharp frames folder for each video.

    img_exts = supported_extensions = tuple('.' + ext.lower() for ext in 'jpg,jpeg,png'.split(','))
    print("First step of refining")
    filter_raw(video_path,frames_path,img_exts,target_count=None,target_percentage=95,groups=1,rename=True)
    filter_raw(frames_path,frames_path,img_exts,target_count=None,target_percentage=20,scalar=3,rename=False)
    print("\n"*3)