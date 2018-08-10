import sys
import threading
import subprocess
import shlex
import os
if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue


class ConvertImg2EXRThread(threading.Thread):
    """
    Thread class used by the converter
    """
    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue

    def run(self):
        while True:
            # grabs data from queue
            (executable, file_in, file_out, overwrite, options) = self.queue.get()
            status = None
            try:
                execute = '"{}" "{}" "{}" {}'.format(executable, file_in, file_out, options)
                if os.path.isfile(file_out) is False or overwrite is True:
                    #subprocess.call( execute )
                    print( "executing: {}".format( execute ))
                else:
                    status = 'File not converted, file already exists and overwrite is set to False.'
            except Exception as e:
                status = str(e)

            # place data into out queue
            self.out_queue.put((file_in, file_out, status))

            # signals to queue job is done
            self.queue.task_done()


def convert_img_2_exr(executable, file_paths, threads = 8, overwrite=False, postfix='_tiled', compression='zips', tile_size=64, linear='off'):
    """This will convert the supplied list of files into tiled exr files.

    Args:
        executable (str): Path to vray img2tiledexr executable, for example : 'C:/Program Files/Chaos Group/V-Ray/Maya 2018 for x64/bin/img2tiledexr.exe'
        file_paths(str[]): List containing the files which need to be converted
                        allowed file types are TGA, PNG, JPG, TIFF, EXR, BMP, HDR, PIC, PSD
        postfix (str): string to add as postfix to the file name
        overwrite (bool): Overwrite existing files?
        compression (str): EXR compression type, allowed values: 'none', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44', 'b44a', 'dwaa', 'dwab'
        tile_size (int): Size of the tiles
        linear (str): Convert color space to linear, allowed values: 'auto', 'on', 'off'

    Returns:
        a tuple containing the orignal file name, the tiled exr file name, and the status string
        a status of None means success, otherwise it will contain the exception string or a
        reason as to why a file wasn't converted.
    """
    in_queue = queue.Queue()
    out_queue = queue.Queue()
    options = '-compression {} -tileSize {} -linear {}'.format(compression, tile_size, linear)

    # spawn a pool of threads, and pass them queue instance
    for i in range(threads):
        thread = ConvertImg2EXRThread(in_queue, out_queue)
        thread.setDaemon(True)
        thread.start()

    for file_in in file_paths:
        file_out = '{}{}.exr'.format(os.path.splitext(file_in)[0], postfix)
        in_queue.put((executable, file_in, file_out, overwrite, options))

    # wait on the queue until everything has been processed
    in_queue.join()

    result = []
    for i in range(out_queue.qsize()):
        result.append(out_queue.get())
    print(result)
    return result

# filenodes = [(filenode, filenode.fileTextureName.get()) for filenode in pm.ls(et=pm.nodetypes.File) if not filenode.fileTextureName.get().lower().endswith('_tiled.exr') and filenode.hasAttr('tiledEXR') and filenode.tiledEXR.get()]

# files = ["P:/Projects/test1/assets/snow/work/lookdev/maya/images/grass_CLR02.tga",
#          "P:/Projects/test1/assets/snow/work/lookdev/maya/images/grass_CLR03.tga",
#          "P:/Projects/test1/assets/snow/work/lookdev/maya/images/grass_CLR01.tga"]
# convert_img_2_exr('C:/Program Files/Chaos Group/V-Ray/Maya 2018 for x64/bin/img2tiledexr.exe', files)
