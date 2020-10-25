import matplotlib.pyplot as plt
from matplotlib.animation import ArtistAnimation

from matplotlib import animation

import numpy as np
fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
artists = []
x = np.arange(10)
for i in range(10):
    y = np.random.rand(10)
    im = ax.scatter(x, y)
    artists.append([im])
print(artists)

anim = ArtistAnimation(fig, artists, interval=1000)

mp4writer = animation.FFMpegWriter(fps=1, metadata=dict(artist='kshibata'), bitrate=1800)
anim.save('test3.mp4', writer=mp4writer)