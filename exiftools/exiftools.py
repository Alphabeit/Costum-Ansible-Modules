#!/usr/bin/python

# created:    20251203 / alphabeit
# lastchange: 20260108 / alphabeit

# Alphabeit https://github.com/Alphabeit
# no license, feel free to use

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: exiftool
short_description: Read and overwrite the label of pictures with exiftool.
description:
    - Allow to read, to save, to print and to overwrite the labels of picture_files.
    - Please install exiftool before at the destination system. 
    - Also you have to ensure, that exiftool is accessible by /usr/bin/exiftool. Please test it before via 'which' or 'whereis'. Maybe you have to create a symlink from '/path/to/exiftool' to '/usr/bin/exiftool'. 
options:
    path:
        description:
            - Path to picture-file(s).
            - Can be a single file, a single picture.
            - Can be a directory, for claiming multiple pictures.
        required: true
        type: str
    suffix:
        description:
            - Desired suffix of picture-file(s), who should addressed.
            - Necessary, when claimed with path a directory.
            - Used Regex Glob (Unix Path Style).
        default: None
        type: str
    metadata:
        description:
            - Define labels to overwrite them on the picture-file(s).
            - Need to get set as key=value => flag='new value'.
            - No template, no control. Any keyword can used as label and will writen with this module.
        type: dictionary
    backup:
        description:
            - By default, exiftool create an copy of each file, before overwriting his labels.
            - We can turn this option of by adding 'backup: False' at our task.
        default: True
        type: bool
author:
    - Alphabeit https://github.com/Alphabeit
'''

EXAMPLES = r'''
# get label from one picture
- name: get labels from fav_photo
  exiftools:
    path: /home/user/pictures/2025/fav_photo.JPG
  register: photo_metadata
  
- name: get infos about picture
  ansible.builtin.debug:
    msg: "Photo shot at {{ item.value.DateTimeOriginal }} in {{ item.value.GPSPosition }} with a {{ item.value.Make }} {{ item.value.Model }}"
  loop: "{{ photo_metadata.exiftools | dict2items }}"
  loop_control:
    label: "{{ item.value.FileName }}"


# get labels from all pictures who ending with .JPG
- name: get labels pictures
  exiftools:
    path: /home/user/pictures/2025
    suffix: '*.JPG'
  register: photo_metadata

- name: get infos about pictures
  ansible.builtin.debug:
    msg: "File {{ item.value.FileName }} named {{ item.value.Title }} was shot by {{ item.value.Artist }}."
  loop: "{{ photo_metadata.exiftools | dict2items }}"
  loop_control:
    label: "{{ item.key }}"


# overwrite 'Title' of photo
- name: overwrite Title
  exiftools:
    path: /home/user/pictures/2025/fav_photo.JPG
    metadata:
      Title: Favorite of all


# overwrite 'Title' of multiple photos, who beginning with DEC*,
# without to clone the pictures before - and print the new Titles   
- name: overwrite Titles
  exiftools:
    path: /home/user/pictures/2025/
    suffix: "DSC0838*"
    metadata:
      Title: Hamburg_New_City
    backup: False
  register: photo_metadata

- name: get infos about picture
  ansible.builtin.debug:
    msg: "New Title is {{ item.value.Title }}."
  loop: "{{ photo_metadata.exiftools | dict2items }}"
  loop_control:
    label: "{{ item.value.FileName }}"
'''

RETURN = r'''
message:
    description: Output message
    returned: always
    type: str
    sample: "Labels are fetched. Can be printed by 'register.exiftools'."

exiftools:
    description: Contains labels and there values from pictures. Saved inside register as '*.exiftools'.
    returned: always
    type: dict
    sample: {"file.JPG": {"label": "value", "label_2": "value", ...}, "file_2.JPG": ... } 

changed:
    description: Whether some labels of pictures got changed.
    returned: When overwriting labels.
    type: bool
    sample: true
'''





from pathlib import Path
from exiftool import ExifToolHelper

def overwrite_labels(path: str, suffix: str, metadata: dict, backup: bool) -> list[str]:

    """
    Allowing to overwrite labels, who being defined by "metadata".

    Parameters:
        path: Can be a file or a directory. Should begin with the root.
        suffix: Glob regex. Important, when path is a directory. Allow to choose multiple pictures.
        metadata: All labels who being defined to get overwritten on pictures.
        backup: Allow to diable creating copies of files before overwriting.

    Returns:
        The list of all pictures, who changed.
    """

    # get file paths as list => following code expect a list
    # with suffix; multiple files
    # without suffix; one file
    if suffix is not None:
        files: list = list(Path(path).rglob(suffix))
    else:
        files: list = [Path(path)]

    # add options to label overwriting
    args = list()
    if not backup:
        args.append("-overwrite_original")
    #  Besides we speak all time about overwriting, exiftool doesn't. In fact, he copies
    # the pictures with the new labels instead. But we can commit to really overwrite the
    # original files. As user, it looks like, there was never created a copy.

    # https://sylikc.github.io/pyexiftool/examples.html#setting-tags
    # with exiftool
    #   rewrite defined labels
    with ExifToolHelper() as et:
        et.set_tags(files, tags=metadata, params=args)
        # files    => addressed picture(s)
        # metadata => labels for overwriting

    # save and return basename of changes files to inform the user
    basenames: list[str] = list()
    for file in files:
        # https://docs.python.org/3/library/pathlib.html#corresponding-tools
        basenames.append(file.name)
    return basenames





def fetch_labels(path: str, suffix: str) -> dict[str, list]:

    """
    Fetching labels of picture(s).

    Parameters:
        path: Can be a file or a directory. Should begin with the root.
        suffix: Glob regex. Important, when path is a directory. Allow to choose multiple pictures.

    Returns:
        A list of all labels of all pictures who addressed.
    """

    # get file paths as list => following code expect a list
    # with suffix; multiple files
    # without suffix; one file
    if suffix is not None:
        files: list = list(Path(path).rglob(suffix))
    else:
        files: list = [Path(path)]

    # https://sylikc.github.io/pyexiftool/examples.html#getting-tags
    # with Exiftool
    #   create dict
    #   foreach file
    #     create entry in dict
    #     fetch labels of file => split dict intro key and value and loop them
    #       shorten label name and save in entry of dict
    # return

    with ExifToolHelper() as et:

        tags = dict()
        #  The module exiftool would return the labels as list[dict]. The handling from
        # dicts inside a list is terrible with ansible. So we want to return a dict[dict], what
        # makes the handling easier. So why we create a dict at first.
        #  At the beginning of the following loop, we add an entry with the filename. That entry
        # get all his labels as dict too.

        for file in files:
            tags.update({f"{file.name}": dict()})
            for label, value in et.get_metadata(file)[0].items():
            #  Get labels as list[dict]. To get the items, we've done two things. First is
            # to decapsulate the list with by returning the first and only index ([0]).
            # Second, by splitting keys and values intro items (.items()). The these get
            # looped as following.

                tags[f"{file.name}"].update({f"{label.split(":")[-1]}": value})
                #  The original label names (as example EXIF:DateTimeOriginal) is too long and would
                # makes trouble while handling. Ansible cant include double points ':' in instructions
                # or conditions. So we shorten the label names.

    # return
    return tags





from ansible.module_utils.basic import AnsibleModule

def run_module():

    """
    Run ansible module "exiftool".

    Returns:
        A list of all labels of all pictures who addressed.
    """

    # define module arguments
    module_args = dict(
        path=dict(type=str, required=True),
        suffix=dict(type=str, default=None),
        metadata=dict(type=dict, default=dict()),
        backup=dict(type=bool, default=True)
    )

    # create result dict
    # set default values
    result = dict(
        changed=False,
        message="Labels are fetched. Can be printed by 'register.exiftools'.",
        exiftools=dict()
    )

    # create AnsibleModule object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # extract parameters
    path: str = module.params['path']
    suffix: str = module.params['suffix']
    metadata: dict = module.params['metadata']
    backup: bool = module.params['backup']

    # change metadata, when metadata is not empty
    #  dict = False
    if metadata:
        changed_labels: list = overwrite_labels(path, suffix, metadata, backup)
        result['changed'] = True
        result['message'] = f"Labels of following pictures got changed: {', '.join(changed_labels)}."

    # read metadata of photos
    labels: dict[str, list] = fetch_labels(path, suffix)
    result['exiftools'] = labels

    # Return results
    module.exit_json(**result)





if __name__ == '__main__':
    run_module()




