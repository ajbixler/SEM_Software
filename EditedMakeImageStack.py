from __future__ import print_function
print('Start')
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'remote'))
import time
import sem
import struct
#import base64
from sem_v3_lib import *
#from io import BytesIO
#import msvcrt
################################################################################

print("So far so good.")

SampleName = 'Sample Name Here'

ImageWidth = 2000

ImageHeight = 2000

ImageOffsetx = 0#-0.2 # in microns

ImageOffsety = 0#0.1  # in microns

DriftCorrx = 0 # microns/frame

DriftCorry = 0 # microns/frame

DriftCorrz = 0 # microns/frame

NumImages = 1

bpp = 16

ScanSpeed = 5

CaptureSE = True

CaptureBSE = True

def ReadMessage(conn):
    # receive the message header

    msg_name = conn._RecvStrD(16)

    hdr = conn._RecvStrD(16)

    v = struct.unpack("<IIHHI", hdr)

    body_size = v[0]



    # get fn name

    cb_name = DecodeString(msg_name)
                     

    # receive the body

    cb_body = conn._RecvStrD(body_size)

        

    # finished reading message

    return (cb_name, cb_body)



def WriteImage(m):

    NumChannels = 0

    if CaptureSE == True:

        SEfile = open(SEFileName, "ab")

        NumChannels += 1

    if CaptureBSE == True:

        BSEfile = open(BSEFileName, "ab")

        NumChannels += 1


    bytes_read = 0

    bytesperpixel = bpp/8

    while bytes_read < ImageWidth*ImageHeight*bytesperpixel*NumChannels:

        (cb_name, cb_body) = ReadMessage(m.connection)

        v = struct.unpack("<IiIiI", cb_body[0:20])

        # Channel 0, write SE image.

        if v[1] == 0 and CaptureSE == True:

            SEfile.write(cb_body[20:])

            bytes_read = bytes_read + v[4]

        # Channel 1, write BSE image.

        if v[1] == 1 and CaptureBSE == True:

            BSEfile.write(cb_body[20:])

            bytes_read = bytes_read + v[4]

        # When we are done, close the files.

        if bytes_read >= ImageWidth*ImageHeight*bytesperpixel*NumChannels:        

            if CaptureSE == True:

                 SEfile.close()

            if CaptureBSE == True:

                 BSEfile.close()

        time.sleep(1)



        im = Image.frombuffer("L", bytes_read, bio, "raw", "L", 0, 1)

        im.save(file_name + ".tif")





def main():

    

    global SEFileName

    global BSEFileName



    # Connect to the SEM SharkSEM interface.

    m = sem.Sem()

    conn = m.Connect('localhost', 8300)

    if conn<0:

        print("Error: Unable to connect to SEM")

        return

        

    ViewField = m.GetViewField()*1000 # View field in microns.

    

    Voltage = m.HVGetVoltage()/1000; # Voltage in keV.



    SEFileName = '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian, SE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)

    BSEFileName = '%s, %d keV, %dx%dx%d, %g um wide, %d bpp, little endian, BSE.raw' % (SampleName, Voltage, ImageWidth, ImageHeight, NumImages, ViewField, bpp)



    # Get rid of any existing files if they are there.  This is an overwrite.

    if CaptureSE == True:

        try:

            os.remove(SEFileName)

        except:

            pass

    if CaptureBSE == True:

        try:

            os.remove(BSEFileName)

        except:

            pass



    # Assign SE to channel 0 and BSE to channel 1.

    m.DtSelect(0, 0)

    m.DtSelect(1, 1)

    # Enable each, 8 or 16 bits/pixel.

    if CaptureSE == True:

        m.DtEnable(0, 1, bpp)

    else:

        m.DtEnable(0, 0)

    if CaptureBSE == True:

        m.DtEnable(1, 1, bpp)

    else:

        m.DtEnable(1, 0)

#    a = m.DtGetEnabled(0)

#    print(a)

#    return;

    

    # make sure scanning is inactive

    m.ScStopScan()

    

    m.ScSetSpeed(ScanSpeed)



    # Note the stage position and apply any initial offset requested.

    (x,y) = m.GetImageShift() # Gives mm.

    

    # Note the working distance.

    WD = m.GetWD() # Gives mm.

    

    time.sleep(1)

    

    # Loop through a bunch of images..

    for i in range(NumImages):

        # Apply drift correction

        ImageCorrx = (ImageOffsetx + DriftCorrx*i)/1000

        ImageCorry = (ImageOffsety + DriftCorry*i)/1000

        ImageCorrz = (DriftCorry*i)/1000

        m.SetImageShift(x+ImageCorrx, y+ImageCorry)

        m.SetWD(WD+ImageCorrz)

        print('Image shift = (%f, %f) microns' % ((x+ImageCorrx)*1000, (y+ImageCorry)*1000))

        print('WD = %f microns' % ((WD+ImageCorrz)*1000))





        # Take an image.

        res = m.ScScanXY(1, ImageWidth, ImageHeight, 0, 0, ImageWidth-1, ImageHeight-1, 1)        

                #print("ScScanXY result: " + str(res))

        print("Scanning image# " + str(i))

        time.sleep(1)



        # Let the image come in as it is acquired and then write it.

        #WriteImage(m, str(V) + "eV_SE.bin")

        WriteImage(m)

        

        print("\n\n")

                

    m.SetImageShift(x, y)
    time.sleep(1)

    

        

    if CaptureSE == True:

        print("\n" + str(i+1) + " images written to " + SEFileName)

    if CaptureBSE == True:

        print("\n" + str(i+1) + " images written to " + BSEFileName)

    

    print('Done')

    

main()



