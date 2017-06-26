# Why?

Different strategies exist to clean up old and unused images on a Docker host:
* Delete images not used by running containers
* Delete images older than some specified date
* Remove *dangling* images (not having any tags)

What I found lacking was a simple way to keep only the latest 1 or 2 images from every repository. This can be very useful for maintaining hosts where you constantly deploy new versions of the same image or hosts where you constantly build new images.

This small script does exactly this
```
usage: docker_imageclean.py [-h] [--yes] [--keep N]

A small utility to cleanup old images on Docker hosts

optional arguments:
  -h, --help  show this help message and exit
  --yes       Assume yes, do not ask for confirmation
  --keep N    Keep the latest N images for each repository
```
