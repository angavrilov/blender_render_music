# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


import bpy, aud
from bpy.app.handlers import persistent

is_rendering = False

@persistent
def play_music(scene):
    global is_rendering
    is_rendering = True

    handle = bpy.types.RenderSettings.music_handle
    addon_prefs = bpy.context.user_preferences.addons[__package__].preferences

    if addon_prefs.use_play:
        if not hasattr(handle, "status") or (hasattr(handle, "status") and handle.status == False):
            print("Playing elevator music...")
            device = aud.device()
            factory = aud.Factory(addon_prefs.playfile)
            bpy.types.RenderSettings.music_handle = device.play(factory)
            handle.loop_count = -1

@persistent
def kill_music(scene):
    global is_rendering
    is_rendering = False

    handle = bpy.types.RenderSettings.music_handle

    if hasattr(handle, "status") and handle.status == True:
        print("Killing elevator music...")
        handle.stop()

@persistent
def end_music(scene):
    handle = bpy.types.RenderSettings.music_handle
    addon_prefs = bpy.context.user_preferences.addons[__package__].preferences
    
    kill_music(scene)
    
    if addon_prefs.use_end:
        device = aud.device()
        factory = aud.Factory(addon_prefs.endfile)
        bpy.types.RenderSettings.music_handle = device.play(factory)

# A hacky way to try detecting bake completion:
#  When idle, scene updates happen continuously on the same frame.
#  However, baking grabs control of the system and sweeps through the range.
#  So detect non-animation continuous streak followed by same frame streak.

last_frame = -1
inc_streak_size = 0
same_streak_size = 0
big_inc_streak_countdown = 0

@persistent
def check_scene_update(scene):
    global last_frame, inc_streak_size, same_streak_size, big_inc_streak_countdown, is_rendering

    prev_frame = last_frame
    frame = scene.frame_current
    last_frame = frame

    if frame == prev_frame + 1:
        same_streak_size = 0
        big_inc_streak_countdown = 0

        if is_rendering or len(bpy.data.screens) == 0 or bpy.data.screens[0].is_animation_playing:
            inc_streak_size = 0
        else:
            inc_streak_size = inc_streak_size + 1

    else:
        if inc_streak_size > 10:
            # Allow for a few random frame changes between inc streak and settling down
            big_inc_streak_countdown = 3

        inc_streak_size = 0

        if frame == prev_frame:
            same_streak_size = same_streak_size + 1

            if same_streak_size > 5 and big_inc_streak_countdown > 0:
                big_inc_streak_countdown = 0

                addon_prefs = bpy.context.user_preferences.addons[__package__].preferences
                if addon_prefs.use_heuristic and not is_rendering:
                    end_music(scene)
        else:
            same_streak_size = 0
            big_inc_streak_countdown = big_inc_streak_countdown - 1
