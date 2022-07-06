# moonraker-timelapse-Cura-PostProcessingScript
A py script to add gcode Command for Timelapse (Octolapse and Moonraker-Timelapse)
It adds gcode to trigger snapshots. 

Triggers could be Layer, Time or number of frames(time based, quite inaccurate :-( ), 

## Install ## 
Copy the file `AddSnapshot.py` in `share/cura/plugins/PostProcessingPlugin/scripts/` folder of Cura directory. Restart Cura.

## Usage ##
![OL-MR_timelapse](https://user-images.githubusercontent.com/88246672/177631145-b4117b84-774f-43c5-a38c-af0174d71ca1.png)

1. start Cura, load your model and configure print settings 
2. select from the menu `Extensions/Post Processing Plugin/Modify G-code`
3. add script `OL-MR Timelapse`
4. choose target `Moonraker-timelapse` or `Octolapse`
5. choose trigger method `Layer`, `Time` or `Nb of frames`
6. Adjust frequency
7. set Custom G-code

## Nota ##
For `Moonraker-timelapse`, Time and Nb of frames methods add `HYPERLAPSE` command instead of the custom g-code  
