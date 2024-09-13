#%% 
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

data = [5, 7, 3, 8, 6]  # Heights of the bars
labels = ['A', 'B', 'C', 'D', 'E']  # Labels for the bars

fig, ax = plt.subplots()

# Create an empty bar chart with initial heights set to zero
bars = ax.bar(labels, [0] * len(data))

# Set the y-axis limit to the maximum value in the data
ax.set_ylim(0, max(data) + 1)

# Function to update the bar heights
def update(frame):
    for i, bar in enumerate(bars):
        if i == frame-1:  # Update only the current frame's bar
            bar.set_height(data[i])

# Create the animation and store it in a variable
anim = FuncAnimation(fig, update, frames=len(data)+1, interval=1000, repeat=False)

# Define the FFmpeg writer with a desired frame rate
writer = FFMpegWriter(fps=1, metadata=dict(artist='Me'), bitrate=1800)

# Save the animation as an MP4 file
anim.save('bar_animation.mp4', writer=writer)

#%% 
from moviepy.editor import TextClip
from PIL import Image, ImageDraw, ImageFont

korean_text = "한글" 

txt_clip = TextClip(korean_text, fontsize=70, font='나눔고딕', color='Red')

# Set duration and position
txt_clip = txt_clip.set_duration(10).set_position('center')

txt_clip = txt_clip.set_fps(24)

# Export the clip
txt_clip.write_videofile("output_with_korean_text.mp4", codec="libx264")

#%%
# import moviepy.editor as mp
# print(mp.TextClip.list('font'))