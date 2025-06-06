from cgitb import reset

import cv2
from tqdm import tqdm
from graphlib import draw_graph
import concurrent.futures
import os
import pickle


class ImageSelector:
    def __init__(self, images):
        self.images = images

        quality_values_path = os.path.split(self.images[0])[0]
        quality_values_file_name = "Image_Qualities.pkl"
        self.quality_values_path = os.path.join(quality_values_path, quality_values_file_name)

        if os.path.exists(self.quality_values_path):
            # If we've previously computed the quality values, load them from the file.
            self.image_fm = self.read_quality_values()
            print("Loaded image quality values from file.")
        else:
            # If we haven't computed the quality values, then do that.
            self.image_fm = self._compute_sharpness_values()
            self.save_quality_values()

    def save_quality_values(self):
        with open(self.quality_values_path, 'wb') as f:
            pickle.dump(self.image_fm, f)

    def read_quality_values(self):
        with open(self.quality_values_path, 'rb') as f:
            data = pickle.load(f)
        # We probably removed some images last time, but this pickle file has all images quality values. We need remove the images we no longer use from this array.
        # print(data[0])
        new_data = []
        for img in data:
            if img[1] in self.images:
                new_data.append(img)



        return new_data

    def _compute_sharpness_values(self):
        print("Calculating image sharpness...")

        def Sharpness_Calc(image):
            r = (self.variance_of_laplacian(cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2GRAY)), image)
            return r

        Images_Iterrable = self.images

        # Using ThreadPoolExecutor to calculate squares concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(tqdm(executor.map(Sharpness_Calc, Images_Iterrable), total=len(Images_Iterrable)))

        # Results are returned in the order of input
        # print(list(results))

        return results

    @staticmethod
    def variance_of_laplacian(image):
        return cv2.Laplacian(image, cv2.CV_64F).var()

    @staticmethod
    def distribute_evenly(total, num_of_groups):
        ideal_per_group = total / num_of_groups
        accumulated_error = 0.0
        distribution = [0] * num_of_groups

        for i in range(num_of_groups):
            distribution[i] = int(ideal_per_group)
            accumulated_error += ideal_per_group - distribution[i]

            while accumulated_error >= 1.0:
                distribution[i] += 1
                accumulated_error -= 1.0

        return distribution, ideal_per_group

    def generate_deleted_images_graph(self, selected_images):
        bins = 100
        step = len(self.images) // bins
        percentages = []

        for i in range(bins):
            start_idx = i * step
            end_idx = (i + 1) * step if i != bins - 1 else len(self.images)
            current_bin = self.images[start_idx:end_idx]
            deleted_count = sum(1 for img in current_bin if img not in selected_images)
            avg = deleted_count / len(current_bin)
            percentages.append(avg * 100)

        draw_graph(percentages, "Distribution of to-be-deleted images")

    def generate_quality_graph(self):
        draw_graph([quality for quality, _ in self.image_fm], "Distribution of image quality")

    def filter_sharpest_images(self, target_count, group_count=None, scalar=1):
        if scalar is None:
            scalar = 1
        if group_count is None:
            group_count = target_count // (2 ** (scalar - 1))
            group_count = max(1, group_count)

        split = len(self.images) / target_count
        ratio = target_count / len(self.images)
        formatted_ratio = "{:.1%}".format(ratio)
        print(f"Requested {target_count} out of {len(self.images)} images ({formatted_ratio}, 1 in {split:.1f}).")

        group_sizes, ideal_total_images_per_group = self.distribute_evenly(len(self.images), group_count)
        images_per_group_list, ideal_selected_images_per_group = self.distribute_evenly(target_count, group_count)

        print(f"Selecting {target_count} image{'s' if target_count != 1 else ''} across {group_count} group{'s' if group_count != 1 else ''}, with total ~{ideal_total_images_per_group:.1f} image{'s' if ideal_total_images_per_group != 1 else ''} per group and selecting ~{ideal_selected_images_per_group:.1f} image{'s' if ideal_selected_images_per_group != 1 else ''} per group (scalar {scalar}).")
        draw_graph([(i % 2) for i in range(group_count)], "Group layout", 100)

        images_per_group_list, _ = self.distribute_evenly(target_count, group_count)

        selected_images = []
        offset_index = 0
        for idx, size in enumerate(group_sizes):
            end_idx = offset_index + size
            group = sorted(self.image_fm[offset_index:end_idx], reverse=True)
            selected_images.extend([img[1] for img in group[:images_per_group_list[idx]]])
            offset_index = end_idx

        self.generate_deleted_images_graph(selected_images)
        self.generate_quality_graph()

        return selected_images
