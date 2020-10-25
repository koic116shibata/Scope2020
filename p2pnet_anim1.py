import networkx as nx
import matplotlib.pyplot as plt
import random
from matplotlib import animation

mp4writer = animation.FFMpegWriter(fps=20, metadata=dict(artist='kshibata'), bitrate=1800)

width = 1024
height = 768
timeLength = 50


fig = plt.figure(figsize=(19.2,10.8),dpi = 100)
G = nx.Graph()

def get_picture(tt):
    plt.clf()
    G.clear()
    col = []
    labelList = {}

    for i in range(0,10):
        ix = random.randrange(0, width)
        iy = random.randrange(0, height)
        G.add_node(i,Position=(ix, iy))
        col.append('#FFC0C0')
        labelList.update({i:('N%d' % i)})

        for j in range(i+1,10):
            G.add_edge(i,j)

    pos = nx.get_node_attributes(G,'Position')

    nx.draw(G,pos,node_color = col, labels = labelList,
            font_size=10, font_color = 'k')

#   get_picture()
#   plt.show()

anim = animation.FuncAnimation(fig, get_picture,  frames=timeLength)
anim.save('test.mp4',writer = mp4writer)