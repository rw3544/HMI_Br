#!/usr/bin/python

import disambiguation
import numpy as np
import sunpy.map
import sunpy.io 
import astropy.io.fits as fits
import pdb
import matplotlib.pyplot as plt
import os


def isLocked(p):
    if os.path.exists(p):
        return True
    try:
        os.mkdir(p)
        return False
    except:
        return True


def pack_to_fits(target, file_name, imageData, headerSrc, y_name, partition, compress=True, whether_flip=True):
    short_name = y_name.split('_', 1)[1]
    parts = file_name.split(".")
    short_name_partition = short_name + partition
    parts[-1:] = [f'{short_name_partition}', f'fits']
    file_name = ".".join(parts)
    file_name = file_name.replace("B_720s", 'HMI')
    save_DIR = os.path.join(target, file_name)
    if not os.path.exists(target):
        os.makedirs(target)
    
    '''
    # Flip the data
    if partition == '_orig_logit':
        imageData = imageData[:, ::-1, ::-1]
    elif y_name == '_mask' or whether_flip == False:
        imageData = imageData
    elif y_name == 'spDisambig_Bt' and partition != '_err':
        imageData = -imageData[::-1, ::-1]
    else:
        imageData = imageData[::-1, ::-1]
    '''
    
    #header0 = (headerSrc[0].header).copy()
    header0 = None
    
    data = [fits.PrimaryHDU(data=None, header=None)]
    data += [fits.CompImageHDU(data=imageData, header=header0)]
    
    hdul = fits.HDUList(data)
    hdul.writeto(save_DIR, overwrite=True)
    


if __name__ == "__main__":
    srcBase = "/scratch/projects/fouheylab/rw3544/download_HMI/data"
    target = "/scratch/projects/fouheylab/rw3544/download_HMI/disambig"

    if not os.path.exists(target):
        os.mkdir(target)

    files = sorted([fn for fn in os.listdir(srcBase) if fn.endswith(".field.fits")])

    for fni,fn in enumerate(files):

        outFile = os.path.join(target, fn.replace(".field.fits",".Bt.npy"))
        if os.path.exists(outFile) or isLocked(outFile+".lock"):
            continue


        print(fni,len(files))
        src = os.path.join(srcBase, fn.replace(".field.fits",".%s.fits"))
        inclination = fits.open(src % "inclination")
        field = fits.open(src % "field")
        disambig = fits.open(src % "disambig")
        sunpymap = sunpy.map.Map(src % "field")

        method = 1 #random method
        azimuth = fits.open(src % "azimuth")

        disambigData = (disambig[1].data // (np.power(2, method))).astype('uint8') % 2
        disambigAdd = disambigData*180.

        C = disambiguation.CoordinateTransform(azimuth, field, inclination, azimuth[1].header, disambigAdd, sunpymap)
        latlon, bptr = disambiguation.CoordinateTransform.ccd(C)

        Bp = bptr[:,:,0].astype(np.float32)
        Bt = bptr[:,:,1].astype(np.float32)
        Br = bptr[:,:,2].astype(np.float32)

        #np.save(os.path.join(target, fn.replace(".field.fits",".Br.npy")), Br) 
        #np.save(os.path.join(target, fn.replace(".field.fits",".Bp.npy")), Bp) 
        #np.save(os.path.join(target, fn.replace(".field.fits",".Bt.npy")), Bt) 
        I0Fn = fn.replace('field.', '')
        pack_to_fits(os.path.join(target, "spDisambig_Bp"), I0Fn, Bp, None, 'spDisambig_Bp', '_HMI', whether_flip=False)
        pack_to_fits(os.path.join(target, "spDisambig_Br"), I0Fn, Br, None, 'spDisambig_Br', '_HMI', whether_flip=False)
        pack_to_fits(os.path.join(target, "spDisambig_Bt"), I0Fn, Bt, None, 'spDisambig_Bt', '_HMI', whether_flip=False)

        os.rmdir(outFile+".lock")

