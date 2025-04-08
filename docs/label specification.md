# Task and Milestone Label Specification

## General Points
- The label uses the text from the `task name` field
- If the task name is blank, then the label is "Unnamed"
- All fields below apply to the Tasks tab

## Label Placement Field
- Inside - label appears inside the task; this option is not available for milestones because they are too short to display most tasks names
- To left - the label is on the same row with, by default, same vertical alignment as task or milestone and a default distance to its left
- To right - the label is on the same row with, by default, same vertical alignment as task or milestone and a default distance to its right
- Above - the label is a default distance above the task or milestone
- Below - the label is a default distance below the task or milestone 
- If a label is longer than an associated task, and it is placed "inside" the task, then the label must be clipped and so its length does not exceed task length
- Clipped labels are truncated with ellipses
- If a label is placed "inside" for a milestone, then the label does not display

## Leader Line Field
- This field is Boolean
- Lets user choose between showing a leader line (if relevant) or not 
- Field is "Yes" by default
- Leader line links the label to associated task or milestone
- No leader line required if placement is "inside"
- If label placement to left then leader line from right end of label and left end of task or milestone
- If label placement to right then leader line from left end of label and right end of task or milestone
- If label placement above then leader line from bottom of label to top of task or milestone; by default horizontal alignment is "centre" of task or milestone
- If label placement below then leader line from top of label to bottom of task or milestone; by default horizontal alignment is "centre" of task or milestone
- If label hide field is "Yes" then no leader line displayed ("No" by default)
- If leader line field is "Yes" then leader line is displayed ("Yes" by default)
- By default, for label placements above or below, leader line is x0.5 row height in length (please add this default to config.py as constant)
- By default, for label placements to left or right, leader line is x1 day width (please add this default to config.py as constant)

## Label Hide Field
- This field is Boolean
- Lets the user choose between showing a label (and, if relevant, leader line) or not
- Field is "No" by default

## Colour Field
- Lets user define colour of label text
- By default, it is black

## Horizontal Alignment Field
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

## Horizontal Offset Field
- Lets the user control how far the label is from the associated task or milestone
- This field only applies to labels placed to the left or to the right
- It is a float type
- The default value is 1.0 (i.e., the same constant referred to earlier)
- The value represents a proportion or multiple of day width (where 1.0 equals x1 day width)
- Negative values are not allowed

## Vertical Offset Field
- Lets the user control how far the label is from the associated task or milestone
- This field only applies to labels placed to above or below associated task or milestone
- It is a float type
- The default value is 0.5 (i.e., the same constant referred to earlier)
- The value represents a proportion or multiple of row height (where 1.0 equals x1 row height)
- Negative values are not allowed