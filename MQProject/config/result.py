import json


class YoloResult:
    labels = []

    class Box:
        def __init__(self, x1, y1, x2, y2):
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2

    @classmethod
    def load_labels(cls, file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                cls.labels = data['labels']
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
        except json.JSONDecodeError:
            print(f"Error: The file {file_path} is not a valid JSON file.")
        except KeyError:
            print(f"Error: The key 'labels' was not found in the JSON file {file_path}.")

    def __init__(self, box, score, label):
        if not isinstance(box, YoloResult.Box):
            raise TypeError("The 'box' parameter must be an instance of YoloResult.box.")
        self.box = box
        self.score = score
        self.label = label


# 加载标签
YoloResult.load_labels('label.json')
