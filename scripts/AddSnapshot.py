# Cura PostProcessingPlugin
# Author:   FbeauKmi    based on DisplayProgressOnLCD by Mathias Lyngklip Kjeldgaard, Alexander Gee, Kimmo Toivanen
# Date:     February 20, 2022
# Modified: February 20, 2022

# Description:  This plugin add custom Snapshot command for octolapse .

from ..Script import Script

import re
import datetime

class AddSnapshot(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "OL-MR Timelapse",
            "description": "Originally built for Octolapse adapted to moonraker-timelapse",
            "key": "AddSnapshot",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "a_target": {
                    "label": "Target timelapse",
                    "description": "Moonraker-timelapse or Octolapse ?",
                    "type": "enum",
                    "options": {
                        "mr": "Moonraker-timelapse",
                        "ol": "Octolapse"
                    },
                    "default_value": "mr"
                },
                "a_trigger": {
                    "label": "Trigger",
                    "description": "Layer or time based timelapse",
                    "type": "enum",
                    "options": {
                        "layer": "Layer",
                        "time": "Time",
                        "fixed": "Nb of snapshot"
                    },
                    "default_value": "layer"
                },
                "b_update_lfrequency":
                {
                    "label": "Layer Interval (experimental)",
                    "description": "Update layer Interval eg: 3 for 1 snapshot every 3 layer, 0.5 for 1 snapshot every 0.5 layers (allowed values 0.1, 0.2, 0.25, 0.35, 0.5)",
                    "unit": "",
                    "type": "float",
                    "min_value": "0.1",
                    "max_value": "10",
                    "default_value":"1",
                    "enabled" : "a_trigger=='layer'"
                },
                "b_update_tfrequency":
                {
                    "label": "Update frequency snapshot",
                    "description": "take snapshot every X seconds",
                    "unit": "s",
                    "type": "int",
                    "min_value": "1",
                    "default_value":"30",
                    "enabled" : "a_trigger=='time'"
                },
                "b_update_nfrequency":
                {
                    "label": "Number of snapshots",
                    "description": "take X snapshots",
                    "unit": "",
                    "type": "int",
                    "min_value": "25",
                    "default_value":"120",
                    "enabled" : "a_trigger=='fixed'"
                },
                "custom_gcode_octolapse":
                {
                    "label": "Custom G-code for Octolapse",
                    "description": "G-code to add to take snapshot.",
                    "type": "str",
                    "default_value": "SNAP",
                    "enabled": "a_target=='ol'"
                },
                "custom_gcode_moonraker":
                {
                    "label": "Custom G-code for Moonraker-timelapse",
                    "description": "G-code to add to take snapshot.",
                    "type": "str",
                    "default_value": "TIMELAPSE_TAKE_FRAME",
                    "enabled": "a_target=='mr'"
                }
            }
        }"""

    # Get the value from a line as a float.
    # Example line ;LAYER_COUNT:120 ;TIME_ELAPSED:1234.6789 or ;TIME:1337
    def getLValue(self, line):
        list_split = re.split(":", line)  # Split at ":" so we can get the numerical value
        return float(list_split[1])  # Convert the numerical portion to a float

    def execute(self, data):
        trigger =  str(self.getSettingValueByKey("a_trigger"))
        target =  str(self.getSettingValueByKey("a_target"))
        layer_number = int(self.getSettingValueByKey("b_update_nfrequency")) - 1
        layer_frequency = float(self.getSettingValueByKey("b_update_lfrequency"))  

        output_frequency = int(self.getSettingValueByKey("b_update_tfrequency"))
        output_gcode = str(self.getSettingValueByKey("custom_gcode_octolapse")) if target=="ol" else  str(self.getSettingValueByKey("custom_gcode_moonraker"))
        
        line_set = {}
        
        first_snapshot = True
        total_time = -1
        previous_layer_end_time = 1
        shot=0
        hyperlapse=0
        
        
        for layer in data:
            layer_index = data.index(layer)
            lines = layer.split("\n")
          
            # escape if HYPERLAPSE
            if hyperlapse == 1:
                  break

            for line in lines:
                
                # escape if HYPERLAPSE
                if hyperlapse == 1:
                  break
                if line.startswith(";TYPE:") and first_snapshot:
                    # Take the first snapshot when encounter ;TYPE: the first time (before skirt, wall, mesh,)
                    fline_index = lines.index(line) + 4
                    # If time base timelapse use HYPERLASPE function of Moonraker
                    if target=="mr" and (trigger=="time" or trigger=="fixed"):
                        lines.insert(fline_index, "HYPERLAPSE ACTION=START CYCLE=" + str(output_frequency))
                        hyperlapse=1
                        break
                    else:
                        lines.insert(fline_index, output_gcode)
                    
                    first_snapshot = False
                
                elif line.startswith(";LAYER_COUNT:"):
                    # This line repersent the total number of layers
                    total_layer = self.getLValue(line)
                     
                
                elif (line.startswith(";TIME:") or line.startswith(";PRINT.TIME:")) and total_time == -1:
                    # This line represents the total time required to print the gcode
                    total_time = int(self.getLValue(line))
                    if trigger=="fixed" and layer_number != -1:
                        output_frequency = int(total_time / layer_number)

                elif line.startswith(";TIME_ELAPSED:"):
                    # We've found one of the time elapsed values which are added at the end of layers
                    # If we have seen this line before then skip processing it. We can see lines multiple times because we are adding
                    # intermediate percentages before the line being processed. This can cause the current line to shift back and be
                    # encountered more than once
                    if line in line_set:
                        continue
                    line_set[line] = True

                    # If total_time was not already found then noop
                    if total_time == -1:
                        continue

                    current_time = int(self.getLValue(line))
                    line_index = lines.index(line)
                    
                    #Layer based snapshot
                    if trigger == "layer":
                        shot = shot + 1
                        # Find next layer to trigger
                        if shot >= int(layer_frequency):
                            # take snapshot 
                            lines.insert(line_index, output_gcode)
                            shot=0
                            
                            if layer_frequency < 1:
                                
                                nb_shot = int(1.0 / layer_frequency) - 1
                                lines_added=1
                                
                                if nb_shot > 0:
                                    for n in range(1,nb_shot + 1):
                                        # Line to add the output
                                        time_line_index = int(float(line_index) * float(n) / (nb_shot+1) ) + lines_added 
                                        # Take snapshot
                                        lines.insert(time_line_index, output_gcode)
                                        # Next line will be again lower
                                        lines_added = lines_added + 1
    
                    else:
                        # Here we calculate remaining time and how many outputs are expected for the layer
                        layer_time_delta = int(current_time - previous_layer_end_time)
                        
                        # If this layer represents less than 1 step then we don't need to emit anything, continue to the next layer
                        if layer_time_delta > output_frequency:
                            # Grab the index of the current line and figure out how many lines represent one second
                            step = line_index / layer_time_delta
                            # Move new lines further as we add new lines above it
                            lines_added = 1
                            # Run through layer in seconds
                            for seconds in range(1, layer_time_delta + 1):
                                # Time from start to decide when to update
                                line_time = int(previous_layer_end_time + seconds)
                                # Output every X seconds and after last layer
                            
                                if line_time % output_frequency == 0 or line_time == total_time:
                                    # Line to add the output
                                    time_line_index = int((seconds * step) + lines_added)

                                    # Take snapshot
                                    lines.insert(time_line_index, output_gcode)
                                    
                                    # Next line will be again lower
                                    lines_added = lines_added + 1

                            previous_layer_end_time = int(current_time)
                    
                    line_index = lines.index(line)
                    if (current_time >= total_time):
                        # Take last snapshot
                        lines.insert(line_index, output_gcode)
                        

            # Join up the lines for this layer again and store them in the data array
            data[layer_index] = "\n".join(lines)
        return data
