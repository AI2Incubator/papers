#!/bin/bash

# Check if Inkscape is installed
if ! command -v inkscape &> /dev/null
then
    echo "Inkscape is not installed. Please install it to proceed."
    exit 1
fi

# Loop through all SVG files in the current directory
for file in *.svg
do
    if [ -f "$file" ]
    then
        echo "Inverting colors of $file..."
        
        # Create a temporary filename
        temp_file="temp_${file}"
        
        # Invert colors using Inkscape and save to temporary file
        inkscape --batch-process --actions="EditSelectAllInAllLayers;org.inkscape.effect.filter.Invert.noprefs;export-filename:$temp_file;export-do;" "$file"
        
        # Check if the inversion was successful
        if [ -f "$temp_file" ]
        then
            # Replace the original file with the inverted one
            mv "$temp_file" "$file"
            echo "Colors inverted successfully for $file"
        else
            echo "Failed to invert colors for $file"
        fi
    fi
done

echo "Color inversion complete for all SVG files in the current directory."
