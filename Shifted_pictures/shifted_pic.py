
from PIL import Image
from mpi4py import MPI
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation, rc

import tracemalloc # for memory tracing

def roll(image, shift = 1):
    return np.roll(image, shift = (shift,shift,shift), axis=0)

def roll_parallel(image, rank , n_proc, step):
    
    width_for_proc = image.shape[1] // n_proc
    last_part_width = image.shape[1] % n_proc

    if rank == n_proc -1:
        start = rank * width_for_proc
        end = (rank+1) * width_for_proc + last_part_width
        #pixels_width_proc = np.arange(rank*width_for_proc, (rank+1)*width_for_proc + last_part_width)
    else:
        start = rank * width_for_proc
        end = (rank+1) * width_for_proc
        #pixels_width_proc = np.arange(rank*width_for_proc, (rank+1)*width_for_proc)
    
    image_part = image[:, start:end ,:]
    image_part = roll(image_part, step)

    return image_part

tracemalloc.start()

path= 'Dream.jpg'

comm = MPI.COMM_WORLD
n_proc = comm.Get_size()
rank = comm.Get_rank()

fig = plt.figure()
image = np.array(Image.open(path))

if rank == 0:
    images = []

data = np.empty_like(image)
times = []
step = 2

for i in range(1, image.shape[0], step):
    
    start = MPI.Wtime()

    data = roll_parallel(image, rank, n_proc, i)
    data = comm.gather(data, root = 0)

    end = MPI.Wtime()

    times.append(end-start)

    if rank == 0:
        img = np.concatenate((data), axis = 1)
        im = plt.imshow(img, animated = True)

        images.append([im])

        # print('Mean time: ', np.mean(times)*1000, ' [sec]')
        # print('current_consumption: ', current,' ')
        # print()

if rank == 0:
    print('Mean time: ', np.mean(times)*1000, ' [sec]')

    current, peak = tracemalloc.get_traced_memory()
    print('current_consumption: ', current,' ')
    print('peak_consumption: ' ,peak)
    tracemalloc.stop()


    ani = animation.ArtistAnimation(fig, images, interval=10, blit=True, repeat_delay=1000)  
    ani.save('shifted_img.gif', writer='pillow', fps=500)
    #ani.save('shifted_img.mp4', writer='pillow', fps=20)
