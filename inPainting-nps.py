import time
import matplotlib.pyplot as plt
import numpy as np
from skimage import io, morphology, exposure, transform, color
from skimage.measure import label, regionprops
#from seed import *
from findMatches import *
from random import randint
import sys
import logging
from logging.config import dictConfig

"""
We implement the pseudo code for the Efros and Leung, Non-Parametric Sampling Texture Analysis
"""

def textureSynthesis(imageFile, windowSize):

    #Reads the image and reduces the value from 0-255 range down to 0-1 range as instructued in the pseudo code
    #Gets the number of rows and coloumns in the the original image
    print(imageFile.split('.')[0]+"-"+str(windowSize)+"-synth.gif")
    img = io.imread(imageFile)
    img = img/255.0
    row, col = np.shape(img)
    #img = color.rgb2gray(img)

    # fill_label = label(filledMap)
    # plt.imshow(fill_label)
    # plt.show()

    #Setting the ErrThreshold, MaxErrThreshold, seed size and the sigma values as mentioned in the NPS pseudo Code
    ErrThreshold = 0.1
    MaxErrThreshold = 0.3
    sigma = windowSize/6.4
    seed = 3
    halfWindow = (windowSize - 1) // 2
    totalPixels = img.shape[0] * img.shape[1]
    print("---------")
    print(img)
    print("---------")
    filledMap = np.ceil(img)
    filledPixels = np.sum(filledMap)

    # Call the conv patches function that returns all the possible candidate patches
    # that can be convolved on from the image for the given windowSize
    convPatches = convolutionPatches_mod(img, filledMap, halfWindow)
    print(convPatches.shape)
    synthesizedImage = img

    # We create a Gaussian Mask of the given windowSize*windowSize for the specified sigma value
    # PSEUDO CODE -----> GaussMask = Gaussian2D(WindowSize,Sigma)
    gaussMask = GaussMask(windowSize,sigma)
    #print(gaussMask)

    synthImagePad = np.lib.pad(synthesizedImage, halfWindow, mode='constant', constant_values=0)
    filledMapPad = np.lib.pad(filledMap, halfWindow, mode='constant', constant_values=0)

    print(filledPixels)
    print(totalPixels)

    while filledPixels < totalPixels:
        progress = False
        pixelList = np.nonzero(morphology.binary_dilation(filledMap) - filledMap)
        neighbors = []
        neighbors.append([np.sum(filledMap[pixelList[0][i] - halfWindow : pixelList[0][i] + halfWindow + 1, pixelList[1][i] - halfWindow : pixelList[1][i] + halfWindow + 1]) for i in range(len(pixelList[0]))])
        decreasingOrder = np.argsort(-np.array(neighbors, dtype=int))

        for i in decreasingOrder[0]:
            template = synthImagePad[pixelList[0][i] - halfWindow + halfWindow:pixelList[0][i] + halfWindow + halfWindow + 1, pixelList[1][i] - halfWindow + halfWindow:pixelList[1][i] + halfWindow + halfWindow + 1]
            validMask = filledMapPad[pixelList[0][i] - halfWindow + halfWindow:pixelList[0][i] + halfWindow + halfWindow + 1, pixelList[1][i] - halfWindow + halfWindow:pixelList[1][i] + halfWindow + halfWindow + 1]
            bestMatches = findMatches(template,convPatches,validMask,gaussMask,windowSize, halfWindow, ErrThreshold)

            bestMatch = randint(0, len(bestMatches)-1)

            if bestMatches[bestMatch][0]<=MaxErrThreshold:
                # PSEUDO CODE -----> Pixel.value = BestMatch.value
                synthImagePad[halfWindow+pixelList[0][i]][halfWindow+pixelList[1][i]] = bestMatches[bestMatch][1]
                synthesizedImage[pixelList[0][i]][pixelList[1][i]] = bestMatches[bestMatch][1]
                filledMapPad[halfWindow+pixelList[0][i]][halfWindow+pixelList[1][i]] = 1
                filledMap[pixelList[0][i]][pixelList[1][i]] = 1
                filledPixels+=1

                # PSEUDO CODE -----> progress = 1
                progress = True
        # PSEUDO CODE -----> if progress == 0
        if not progress:
            # PSEUDO CODE -----> then MaxErrThreshold = MaxErrThreshold * 1.1
            MaxErrThreshold *= 1.1
        i = (filledPixels/totalPixels)*100
        sys.stdout.write("\r%d%%" % i)
        sys.stdout.flush()
    io.imsave(imageFile.split('.')[0]+"-"+str(windowSize)+"-synth.gif", synthesizedImage)
    plt.show()
    return


def GaussMask(windowSize, sigma):
    # This creates an windowSize*windowSize square 2D gaussian mask for a given value of sigma
    # PSEUDO CODE -----> GaussMask = Gaussian2D(WindowSize,Sigma)
    x, y = np.mgrid[-windowSize//2 + 1:windowSize//2 + 1, -windowSize//2 + 1:windowSize//2 + 1]
    g = np.exp(-((x**2 + y**2)/(2.0*sigma**2)))
    return g/g.sum()


def convolutionPatches_mod(img, filledMap, halfWindow):
    #Finds and stores all the possibel convolution patches possible for each given pixel
    convPatches = []
    c = 0
    for i in range(halfWindow, img.shape[0] - halfWindow - 1):
        for j in range(halfWindow, img.shape[1] - halfWindow - 1):
            if 0 in filledMap[i - halfWindow:i + halfWindow + 1, j - halfWindow: j + halfWindow + 1]:
                c = c + 1
            else:
                convPatches.append(np.reshape(
                    img[i - halfWindow:i + halfWindow + 1, j - halfWindow: j + halfWindow + 1],
                    (2 * halfWindow + 1) ** 2))
    convPatches = np.double(convPatches)
    return convPatches



if __name__ == '__main__':

    windowSize = 11
    textureSynthesis("img/test_im1.bmp", windowSize)
    #end = time.time()
    #logging.info("\t"+file+"-"+str(windowSize)+"\t:-  "+str(end-start)+" secs")
