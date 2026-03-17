# keystore for nexus 
> Ansible Module



## Describtion

When using a Nexus Repository Manager (Nexus) and RetHat Enterprise Linux (RHEL) systems, it 
could be for intrest to use the Nexus, to proxy the packages of the RHEL sources. 

In that case, the Nexus require a certificate (Keystore) created by a RHEL system with an active 
subscription.

See also https://help.sonatype.com/en/proxying-rhel-yum-repositories.html for more infos by
Sonatype (Company behind Nexus).



## Attention

This Ansible module is made for creating and receiving these Keystore files. 

It will only create the Keystore files, receive and offers them by ```REGISTER.content_keystone```
(see examples) in ```base64``` encoding. It didint load them into the Nexus Store (you have to do 
this by you own). Please dont forget you have to decode them back from ```base64```. 

The moudle have to get executed on a RHEL system with an active subscription. Created and testet 
was the module on a RHEL 10 system.



## Requirments

Please ensure:
- openssl is installed.
- keystore is installed.
- Destination System is a RHEL system and have an active subscription.
- Module is correct loaded (I placed it intro the ../libary).
```text
  ├── inventory
  │   └── inventory.ini
  ├── library                   <- 
  │   └── keystore_for_nexus.sh <- 
  ├── playbooks
  │   ├── ansible.cfg
```



## Example

```yaml
- name: create and read keystore
  keystore_for_nexus:
    password: "pa$$w0rd"
  delegate_to: RHEL10_0815
  register: keystore_value

- name: save keystore on nexus
  ansible.builtin.copy:
    dest: /etc/nexus/store/keystore.p12
    content: "{{ keystore_value.content_keystone | b64decode }}"
    owner: nexus
    group: nexus
    mode: 0644
  delegate_to: NEXUS
```

