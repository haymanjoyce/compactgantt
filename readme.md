# Project Planning Tool

## Purpose

The purpose of the tool is to enable me, the user, to squeeze as much project-planning related information onto one page as possible.

## Problem

The problems that I have with existing tools include, for example:

 - I can only fit one task per row
 - I cannot change magnification at points on the scale (so I cannot show tasks in distant future at a lower magnification)
 - I cannot be selective about applying (and placing) labels and logic (i.e., connectors)
 - I lack fine control over the dimensions and so it's often hard to get the chart to fit on the desired paper or slide
 - I have to hand draw my charts (using PowerPoint, for example) which is time-consuming and error-prone
 - Planning tool Gantt charts are generally pretty ugly which makes them less engaging to look at

## Chart Design

### Layout Components

 - outer_frame - control of overall dimensions of inked area; user can apply un-inked margins (i.e. offsets)

 - header_frame - sits at top of outer_frame; contains headers; full width of outer_frame
 - header - row within header_frame that contains text; can be stacked

 - footer_frame - sits at bottom of outer_frame; contains footers; full width of outer_frame
 - footer - row within footer_frame that contains text; can be stacked

 - inner_frame - sits between header_frame and footer_frame; full width of outer_frame
 - time_frame - sits inside inner_frame; time_frames show chart at different levels of magnification

 - scale_frame - sits inside a time_frame; contains scales; full width of time_frame; typically above row_frame
 - scale - sits inside scale_frame; defines a scale for the time_frame; can stack multiple scales

 - row_frame - sits inside a time_frame; contains rows; full width of inner_frame; typically below scale_frame 
 - row - sits inside row_frame; defines a row for the chart; stacked vertically

 - swimlane - sits in inner_frame; can be used to group rows visually; full width of inner_frame

### Subcomponents

 - gridlines - applied to row_frame; can be horizontal, vertical, or both
 - task - multiple tasks can be assigned to a row
 - milestone - assigned to a row
 - label - user defined text box; associated with a task, milestone, or connector
 - connector - line showing flow of logic between a task and/or milestone
 - text_box - user defined text boxes; can be placed anywhere
 - curtain - user defined time interval; can be placed anywhere inside a row_frame
 - pipe - user defined time point; can be placed anywhere inside a row_frame

### Excluded Features

 - tasklist - not sure that we want this feature because it requires one task per row
 - legend - user can define placement; not sure that we want this feature

### Design Notes

 - If there is one time_frame in the inner_frame, then it is the same width as the inner_frame
 - If there are multiple time_frames in the inner_frame, then they are stacked horizontally (i.e., left to right)
 - The width of the time_frame is defined by the user as a proportion of the inner_frame width
 - The first time_frame from the left will, typically, be the most detailed (i.e., highest magnification)
 - Multiple time_frames must have the same number of scales and rows, and they must align
 - The first part of a task might appear in one time_frame and the second part in a neighbouring time_frame
 - The user can define the number of scales and rows in a time_frame
 - A curtain may start in one time_frame and end in another

## User Interface Requirements

 - User will need tabs in the data entry window for defining these components:
   - tasks - will define task and milestone data including name, start, end, duration, etc.
   - connectors - will show logic driving tasks and milestones
   - curtains & pipes - we can use same table to define time intervals (curtains) and time points (pipes)
   - swimlanes - will define swimlanes; can also be used to colour or label a row, for example
   - text boxes - will define user-defined text boxes
   - headers & footers - will define headers and footers
   - scales - user can define scales here (e.g. colouring, labelling, units, etc.)

 - User will need a dialogue box (maybe more than one) for defining general layout:
   - outer_frame - dimensions user defined
   - header_frame - height user defined
   - footer_frame - height user defined
   - inner_frame - dimension is calculated
   - time_frames - user defines number of time_frames and their start and finish dates; up to three time_frames
   - scale_frames - height determined by number of scales it contains; assign chosen scales used here (up to three)
   - row_frame - dimension is calculated
   - rows - number of rows is user defined but height determined by row_frame

 - Will need other kinds of dialogue box or window for defining these components:
   - gridlines - user defined; may be horizontal, vertical, or both
