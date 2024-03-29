import numpy as np
import cv2
from matplotlib import pyplot as plt


img1 = cv2.imread('im1.jpg', 0)
img2 = cv2.imread('im2.jpg',0)

h1, w1 = img1.shape[:2]
h2, w2 = img2.shape[:2]

# A threshold to decide if there are sufficient putative matching keypoint pairs
MIN_MATCH_COUNT = 10

# Initiate BRISK detector
brisk =   cv2.BRISK_create()

# Find the keypoints and descriptors with BRISK
kp1, des1 = brisk.detectAndCompute(img1,None)
kp2, des2 = brisk.detectAndCompute(img2,None)

# initialize Brute-Force matcher
bf = cv2.BFMatcher()

# use KNN match of Brute-Force matcher for descriptors
matches = bf.knnMatch(des2,des1, k=2)


#exclude outliers
# Apply ratio test (see Lowe's paper). Here we use dr = 1 to accept all the NN matches
good = []
dr = 0.8
for m,n in matches:
    
    if m.distance < dr * n.distance:
        good.append(m)

print ('matches num',len(matches))
print ('good matches num',len(good))	
		



if len(good) > MIN_MATCH_COUNT:

  src_pts = np.float32([ kp2[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
  dst_pts = np.float32([ kp1[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
  
  # Compute homography matrix M and the inliers/outliers are stored in mask
  M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 1.0)
  matchesMask = mask.ravel().tolist()

else:
  print "Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT)
  matchesMask = None

if matchesMask:
    
  # Initialize a matrix to include all the coordinates in the image, from (0, 0), (1, 0), ..., to (w-1, h-1)
  # In this way, you do not need loops to access every pixel
  
  # Calculate the new image coordinates based on the homography matrix
  c = np.zeros((3, h2*w2), dtype=np.int)
  for y in range(h2):
    c[:, y*w2:(y+1)*w2] = np.matrix([np.arange(w2), [y] * w2,  [1] * w2])
  new_c = M * np.matrix(c)
  new_c = np.around(np.divide(new_c, new_c[2]))

  # The new coordinates may have negative values. So perform translation if necessary
  x_min = int(np.amin(new_c[0]))
  y_min = int(np.amin(new_c[1]))
  x_max = int(np.amax(new_c[0]))
  y_max = int(np.amax(new_c[1]))
  if x_min < 0:
    t_x = -x_min
  else:
    t_x = 0
  if y_min < 0:
    t_y = -y_min
  else:
    t_y = 0

  # Initialize the final image to include every pixel of the stitched images  
  new_w = int(np.maximum(x_max, w1) - np.minimum(x_min, 0) + 1)
  new_h = int(np.maximum(y_max, h1) - np.minimum(y_min, 0) + 1)

  new_img1 = np.zeros((new_h, new_w), dtype=np.uint8)
  new_img2 = np.zeros((new_h, new_w), dtype=np.uint8)

  # Assign the first image
  new_img1[t_y:t_y+h1, t_x:t_x+w1] = img1

  # Assign the second image based on the newly calculated coordinates
  for idx in range(c.shape[1]):
    x = c[0, idx]
    y = c[1, idx]
    x_c = int(new_c[0, idx])
    y_c = int(new_c[1, idx])
    new_img2[y_c + t_y, x_c + t_x] = img2[y, x]

  # The stitched image
  new_img = (new_img1 + new_img2) / 2
  cv2.imwrite('stitched_img.jpg', new_img);
  cv2.imshow("Stitched Image", new_img)
  cv2.waitKey()
  cv2.destroyAllWindows()
