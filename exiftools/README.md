# exiftools (Ansible Module)

An Ansible module to read, save, print and overwrite labels of pictures with ```exiftool```. 

Please consider, I didnt created ```exiftool``` itself. I'm just a guy who made a program of top of another programs. So please visit also the https://exiftool.org/ and https://pypi.org/project/PyExifTool/ which I used.



## Install

Save the exiftools.py inside you module-folder, of your Ansible code. Mostly the ```/librar``` folder.

```text
├── inventory
│   └── inventory.ini
├── library <-
│   └── exiftools.py <-
├── playbooks
│   ├── ansible.cfg
│   ├── debug_exiftool.yaml
```

Please also ensure, ```exiftool``` is installed on the destination system. Additional its important that ```exiftool``` is accessible by ```/usr/bin/exiftool```. You can test it with ```which``` or ```whereis```. So maybe, you have to create a symlink.



## Module Options

```yaml
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
```



## Examples

```yaml
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
```



## Returns

```yaml
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
```
