# Task and Milestone Label Specification

## General Points
- The label uses the text from the `task name` field
- If the task name is blank, then the label is "Unnamed"
- In this iteration, there is no automatic handling over overlapping labels
- Vertical alignment of labels may look off because text sits on text baseline
- To compensate for this, text may need to be moved down by half its height

## Label Fields:

### Label Placement Field
- Inside - label appears inside the task; this option is not available for milestones because they are too short to display most tasks names
- To left - the label is on the same row with, by default, same vertical alignment as task or milestone and a default distance to its left
- To right - the label is on the same row with, by default, same vertical alignment as task or milestone and a default distance to its right
- Above - the label is a default distance above the task or milestone
- Below - the label is a default distance below the task or milestone 
- If a label is longer than an associated task, and it is placed "inside" the task, then the label must be clipped and so its length does not exceed task length
- Clipped labels are truncated with ellipses
- Labels are clipped automatically if they are longer than the associated task
- Label length is determined, in first instance, by using `svgwrite`'s `text_length` method and then by estimating based upon the number of characters and font size
- If a label is placed "inside" for a milestone, then the label does not display (i.e., no rendered)
- Default distances between label and task or milestone are:
  - To left: 1.0 day width
  - To right: 1.0 day width
  - Above: 0.5 row height
  - Below: 0.5 row height

### Label Hide Field
- This field is Boolean
- Lets the user choose between showing a label (and, if relevant, leader line) or not
- Field is "No" by default

### Label Text Colour Field
- Lets user define colour of label text
- By default, it is black
- Field accepts hexadecimal colour codes (e.g., #000000 for black, #FFFFFF for white)
- Field accepts colour names (e.g., "red", "blue", "green")
- Field accepts RGB tuples (e.g., (255, 0, 0) for red)
- Field will require validation to ensure the colour is valid
- If validation fails, the field will revert to the default colour (black)

### Label Alignment Field
- Options: Left, Centre, Right
- Rules by Placement:
  - **Inside**:
    - Left: Label is left-aligned inside the task.
    - Centre: Label is centre-aligned inside the task, but only if the task is wider than the label; otherwise, defaults to Left.
    - Right: Label is right-aligned inside the task, but only if the task is wider than the label; otherwise, defaults to Left.
  - **To left**:
    - Always aligned Right (text is as close as possible to the leader line); Left and Centre do not apply.
  - **To right**:
    - Always aligned Left (text is as close as possible to the leader line); Centre and Right do not apply.
  - **Above**:
    - Left: Label text is positioned to the left of the leader line (leader line remains centred with task or milestone).
    - Centre: Label text is horizontally centred with the leader line and task or milestone.
    - Right: Label text is positioned to the right of the leader line (leader line remains centred with task or milestone).
  - **Below**:
    - Left: Label text is positioned to the left of the leader line (leader line remains centred with task or milestone).
    - Centre: Label text is horizontally centred with the leader line and task or milestone.
    - Right: Label text is positioned to the right of the leader line (leader line remains centred with task or milestone).
- For Above/Below placement, if the label is wider than the task or milestone, no clipping required in this iteration

### Label Horizontal Offset Field
- Lets the user control how far the label is from the associated task or milestone
- This field only applies to labels placed to the left or to the right
- It is a float type
- The default value is 1.0 (i.e., the same constant referred to earlier)
- The value represents a proportion or multiple of day width (where 1.0 equals x1 day width)
- Negative values are not allowed
- This offset is the gap between the task/milestone edge and the label’s closest edge (after alignment)
- So for To Right placement, the gap is x_end + (offset * day_width) to the label’s left edge

### Label Vertical Offset Field
- Lets the user control how far the label is from the associated task or milestone
- This field only applies to labels placed to above or below associated task or milestone
- It is a float type
- The default value is 0.5 (i.e., the same constant referred to earlier)
- The value represents a proportion or multiple of row height (where 1.0 equals x1 row height)
- Negative values are not allowed
- For clarification, vertical offset is the gap from the task/milestone’s top/bottom to the label’s bottom/top, respectively
- So for Above, the gap is y_task - (offset * row_height) to the label’s bottom

## Label Leader Line
- Note, this is a feature and not a field
- Leader line links the label to associated task or milestone
- Labels leaders are always shown except when label is placed "inside" the task or milestone or when the label hide field is "Yes"
- No leader line required if placement is "inside"
- If label placement to left then leader line from right end of label and left end of task or milestone
- If label placement to right then leader line from left end of label and right end of task or milestone
- If label placement above then leader line from bottom of label to top of task or milestone; by default horizontal alignment is "centre" of task or milestone
- If label placement below then leader line from top of label to bottom of task or milestone; by default horizontal alignment is "centre" of task or milestone
- If label hide field is "Yes" then no leader line displayed ("No" by default)
- By default, for label placements above or below, leader line is x0.5 row height in length (please add this default to config.py as constant)
- By default, for label placements to left or right, leader line is x1 day width (please add this default to config.py as constant)
- Suggested constant names: 'LEADER_LINE_VERTICAL_DEFAULT' and 'LEADER_LINE_HORIZONTAL_DEFAULT'
- In this iteration, the user cannot define leader line style; default style is a solid black line, 1px wide
- Note, in case it is not clear, label leader lines should either be exactly vertical or horizontal in orientation

## Tasks Tab

In this design, the fields on the task tab are as follows:
- `task id` - Integer (e.g., 1) and auto-generated from row index (1-based) (hidden field)
- `task name` - String (e.g., "Design Phase")
- `start date` - Date (e.g., 2025-01-05)
- `finish date` - Date (e.g., 2025-01-15)
- `row number` - Integer (e.g., 1)
- `label placement` - String (e.g., "Inside", "To left", "To right", "Above", "Below")
- `label hide` - Yes/No (e.g., "No", default is "No")
- `label alignment` - String (e.g., "Left", "Centre", "Right")
- `label horizontal offset` - Float (e.g., 1.0)
- `label vertical offset` - Float (e.g., 0.5)
- `label text colour` - String (e.g., "#FF0000" for red)