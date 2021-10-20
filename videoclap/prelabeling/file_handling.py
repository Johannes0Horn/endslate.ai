import os


def create_directory_structure_video(root_dir, project_name):
    create_root_dir(root_dir)
    project_dir = create_project_dir(root_dir, project_name)
    ann_dir = create_ann_dir(project_dir)
    img_dir = create_video_dir(project_dir)

    return project_dir, ann_dir, img_dir


def create_directory_structure(root_dir, project_name):
    create_root_dir(root_dir)
    project_dir = create_project_dir(root_dir, project_name)
    ann_dir = create_ann_dir(project_dir)
    img_dir = create_img_dir(project_dir)

    return project_dir, ann_dir, img_dir


def create_root_dir(root_dir):
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)


def create_project_dir(root_dir, project_name):
    project_dir_path = os.path.join(root_dir, project_name)

    if not os.path.exists(project_dir_path):
        os.mkdir(project_dir_path)

    return project_dir_path


def create_ann_dir(project_dir_path):
    ann_dir_path = os.path.join(project_dir_path, "ann")

    if not os.path.exists(ann_dir_path):
        os.mkdir(ann_dir_path)

    return ann_dir_path


def create_video_dir(project_dir_path):
    img_dir_path = os.path.join(project_dir_path, "video")

    if not os.path.exists(img_dir_path):
        os.mkdir(img_dir_path)

    return img_dir_path


def create_img_dir(project_dir_path):
    img_dir_path = os.path.join(project_dir_path, "img")

    if not os.path.exists(img_dir_path):
        os.mkdir(img_dir_path)

    return img_dir_path
