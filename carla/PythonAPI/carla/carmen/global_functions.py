#!/usr/bin/env python

# Global Functions for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.



# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

def clamp_to_range(value, min, max):
     return (value % (max - min)) + min

def clamp_to_direction(value):
    if value > 90:
        value = 180 - value
    elif value < -90:
        value = value + 180
        value = - value
    return value