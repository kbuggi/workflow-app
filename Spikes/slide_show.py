"""
Slideshow originally intended to be a built-in viewer of media files for a recipe.
This didn't work well, especially switching image->video->image.
Instead create an XSPF file containing and invokes VLC.
VLC allows the image & video files to be remote, but the code here assumes they have been downloaded locally.

https://xspf.org/quickstart 
"""

import sys, os, platform
import json
import filetype    # pip install filetype
import tempfile
import shutil
import atexit
from pathlib import Path
from datetime import datetime, timezone
import subprocess, time

import argparse



# Configure module-level logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Add a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Optional: add a formatter so messages look nicer
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

logger.info("Started")

class MediaItem:

    def __init__(self, dictionary, media_path=""):
        self.caption = dictionary.get("caption","")
        self.path = dictionary.get("path","")
        self.type = None
        self.next = None
        self.prev = None
        logger.debug(f"MediaItem: {self.path} {media_path} {self.caption}")
        if self.path=="":
            warning = f"Unable to process item in ablum with caption '{self.caption}' - no filename!"
            logger.exception(warning)
            raise ValueError (warning)
        self.path = os.path.join(media_path, self.path)
        try:
            os.stat(self.path) #this will raise FileNotFoundError error if not exists
            kind = filetype.guess(self.path)
        except FileNotFoundError as e:
            warning = f"Unable to process item in ablum with filename '{self.path}' - {e}"
            logger.exception(warning)
            raise ValueError (warning)
        if kind is None:
            warning = f"Unable to process item in ablum with filename '{self.path}' - unknown media type"
            logger.exception(warning)
            raise ValueError (warning)
        logger.info(f'File type: {kind.mime}')  # Examples: 'image/jpeg' and 'video/mp4'
        if  "image" not in kind.mime and "video" not in kind.mime:
            warning = f"Unable to process item in ablum with filename '{self.path}' - unsupported type {kind.mime}"
            logger.exception(warning)
            raise ValueError (warning)
        self.type=kind.mime
          
        
    def __str__(self):
        return f"MediaItem: '{self.path}' with caption '{self.caption}' of mimetype '{self.type}'"

    def __repr__(self):
        return f'MediaItem("{self.dictionary}")'
    
    @property
    def abspath(self):
        return os.path.abspath(self.path)
    
    @property
    def xspf(self)->str:
        return f"""
            <track>
                <location>{self.abspath}</location>
                <title>{self.caption}</title>
            </track>
        """
        

    





class PhotoAlbum:
    def __init__(self, album_file, album_title="", media_path=""):
        self.album_file = album_file
        self.album_title = album_title if album_title!="" else album_file
        self.album_media_item_list = []
        self.media_path = media_path if media_path!="" else os.getcwd()

        logger.info(f"opening {self.album_file}")
        logger.info(f"media_path {self.media_path}")

        with open(self.album_file, "r") as f:        
            self.album_json = json.load(f)
        if len(self.album_json)==0:
            warning=f"Invald format PhotoAlbum '{self.album_json}' "
            logger.error(warning)
            raise ValueError ( warning )

    def __iter__(self):
        """Allows enumeration by iterating over album_media_item_list."""
        return iter(self.album_media_item_list)


    def build(self):
        self.first_item = None
        warnings=[]
        for index, item in enumerate(self.album_json):
            try:
                next_item = MediaItem(item, media_path=self.media_path)
            except ValueError as e:
                warnings.append(f"Item {index+1}: {e}")
                next_item = None
                continue
            except FileNotFoundError as e:
                warnings.append(f"Item {index+1}: {e}")
                next_item = None
                continue
            self.album_media_item_list.append(next_item)
            if not self.first_item:
                self.first_item = next_item
                current_item = next_item
            else:
                current_item.next = next_item
                next_item.previous = current_item
                current_item = next_item
        if not self.first_item:
            warning=f"No valid entries found in PhotoAlbum '{self.album_file}' "
            logger.error(warning)
            #raise ValueError ( warning )
        #current_item is the last item found; point it to first item to make list circular
        current_item.next = self.first_item
        self.first_item.previous = current_item
        return warnings

    """ create vlc playlist including absolute paths & call vlc using default blocking or non-blocking approach """

    def open_in_vlc(self):
        self.open_in_vlc_blocking()


    """ create vlc playlist including absolute paths & call vlc - BLOCKING    """

    def open_in_vlc_blocking(self):
        process = self.open_in_vlc_non_blocking()
        #could do process.wait()
        count=1
        while process.poll() is None:
            if count % 12 == 0:
                #only log every 2 mins
                logger.info( f"VLC still running ..." )
            count += 1
            time.sleep(10)
        logger.info( f"VLC finished at {datetime.now()}")
        logger.info( f"VLC finished wuth exit_code {process.returncode}")



    """ create vlc playlist including absolute paths & call vlc - NON-BLOCKING    """

    def open_in_vlc_non_blocking(self):
        # Playlist file
        playlist_path = self.generate_xspf_file()    

        # Path to VLC
        vlc_path_mac = '/Applications/VLC.app/Contents/MacOS/VLC'  # macOS path
        vlc_path_win = r'C:\Program Files\VideoLAN\VLC\vlc.exe'   # Windows path

        os_name = platform.system().lower()

        if os_name == 'darwin':  # macOS
            args = [ vlc_path_mac, playlist_path, "--loop", "--fullscreen"]

        elif os_name == 'windows':  # Windows
            args = [ vlc_path_win, playlist_path, "--loop", "--fullscreen]

        else:
            error = f"Unable to launch VLC; Unsupported OS {os_name}"
            logger.exception(error)
            raise ValueError(error)

        logger.info( f"VLC arguments {args}" )    
        logger.info( f"Starting VLC at {datetime.now() }..." )    
        process = subprocess.Popen (args)

        logger.info( f"VLC started at {datetime.now() } ..." )
        logger.info( f"VLC started with process_id {process.pid}" )
        return process
    









    """ xspf is a open playlist format accepted by vlc"""
    def generate_xspf_file(self,filename="photoalbum.xspf")->str:
        contents=self.generate_xspf_file_contents()
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Temporary directory: {temp_dir}")
        if not filename.endswith(".xspf"):
            error=f"VLC requires filename to end with '.xspf' - '{filename}' is invalid"
            logger.exception(error)
            raise ValueError(error)
        #no try/catch - this should always succeed
        path = Path(temp_dir) / filename
        with open(path, 'w') as f:
            f.write(contents)
        logger.info(f"created xspf file {path}")
        return path
        # Register cleanup function to delete the temp directory on exit
        #atexit.register(lambda: shutil.rmtree(temp_dir))
        

  
    def generate_xspf_file_contents(self)->str:
        body=""
        for m in self.album_media_item_list:
            body += m.xspf
        now = datetime.now(timezone.utc).isoformat()
        header=f"""<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
    <!-- title of the playlist -->
    <title>{self.album_title}</title>

    <!-- name of the author -->
    <creator>slide_show.py</creator>

    <!-- homepage of the author -->
    <info>https://www.qmul.ac.uk</info>

    <!-- creation date formatted as an XML schema dateTime  -->
    <date>{now}</date>

    <!-- comment  -->
    <annotation>Created by slide_show.py</annotation>

    <trackList>
"""
        footer="""
    </trackList>
</playlist>

"""
        return header + body + footer



    

        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runs a slideshow defined in JSON file")

    # Define arguments
    parser.add_argument("filename", help="slideshow in json/jsonc format (required)")
    parser.add_argument("-f", "--folder", type=str, help="folder where media is held if not working directory (optional)")
    args = parser.parse_args()
    logger.info(f"Processing slideshow {args.filename}")
    media_folder = args.folder if args.folder else os.getcwd()

    p=PhotoAlbum(args.filename, media_path=media_folder)
    try:
        warnings=p.build()
        logger.info(warnings)
        logger.info("Finished PhotoAlbum")
        print(p)
        repr(p)

    except Exception as e:
        logger.error(f"stuff went wrong: {e}")
    

    #Check the linked list (original approach)
    first_item = p.first_item
    item = p.first_item
    while item:
        logger.info(f"item:{item}")
        item = item.next
        if item == first_item:
            item=None #break the loop 

    p.open_in_vlc()


    sys.exit(0)






