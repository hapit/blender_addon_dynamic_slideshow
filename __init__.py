'''
Copyright (C) 2015 Philipp Hemmer
phedev@gmail.com

Created by Philipp Hemmer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Dynamic Slideshow",
    "author": "Philipp (Hapit) Hemmer",
    "version": (0, 7),
    "blender": (2, 79, 0),
    "location": "View3D > Tool shelf > Slideshow (Tab)",
    "description": "Addon for creating dynamic slideshows. Inspired by a CG Cookie Tutorial, this addon creates cameras and sequences for a slideshow. It uses the 'images as planes' addon for adding pictures.",
    #"warning": "",
    "wiki_url": "https://github.com/hapit/blender_addon_dynamic_slideshow/wiki/Documentation",
    'tracker_url': 'https://github.com/hapit/blender_addon_dynamic_slideshow/issues',
    'support': 'COMMUNITY',
    "category": "Tools"}


from . import developer_utils
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

import bpy,bgl,blf
from . registration import register_all, unregister_all


def register():
    bpy.utils.register_module(__name__)
    register_all()
    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))


def unregister():
    bpy.utils.unregister_module(__name__)
    unregister_all()
    print("Unregistered {}".format(bl_info["name"]))
