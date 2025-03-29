# Project Planning Tool

## Purpose

The purpose of the tool is to enable me, the user, to squeeze as much project-planning related information onto one page as possible.

## Problem

The problems that I have with existing tools include, for example:

 - I can only fit one task per row
 - I cannot change magnification at points on the scale (so I cannot show tasks in distant future at a lower magnification)
 - I cannot be selective about applying (and placing) labels and logic (i.e., connectors)
 - I lack fine control over dimensions and so it's often hard to get a chart to fit on the desired paper or slide
 - I have to hand draw my charts (using PowerPoint, for example) which is time-consuming and error-prone
 - Planning tool Gantt charts are generally pretty ugly which makes them less engaging to look at

## Chart Design

### Layout Components

 - outer_frame - control of overall dimensions of inked area; user can apply un-inked margins (i.e. offsets)
 - header - sits at top of outer_frame; full width of outer_frame; only one header row available (design decision)
 - footer - sits at bottom of outer_frame; full width of outer_frame; only one footer row available (design decision)
 - inner_frame - sits between header_frame and footer_frame; full width of outer_frame
 - time_frame - sits inside inner_frame; time_frames able to show chart at different levels of magnification
 - upper_scale - sits inside time_frame; shows the timescale; full width of time_frame; placed at top of time_frame
 - lower_scale - sits inside time_frame; shows the timescale; full width of time_frame; placed below upper_scale
 - row_frame - sits inside a time_frame; contains rows; full width of inner_frame; placed below lower_scale
 - row - sits inside row_frame; can be multiple rows; full width of row_frame; users defines number of rows
 - swimlane - sits in inner_frame; can be used to group rows visually; full width of inner_frame

### Subcomponents

 - gridlines - applied to row_frame; can be horizontal, vertical, or both
 - task - multiple tasks can be assigned to a row
 - milestone - assigned to a row
 - connector - line showing flow of logic between a task and/or milestone
 - text_box - user defined text boxes; can be placed anywhere
 - curtain - user defined time interval; can be placed anywhere inside a row_frame
 - pipe - user defined time point; can be placed anywhere inside a row_frame

### Design Notes

 - If there is one time_frame in the inner_frame, then it is the same width as the inner_frame
 - If there are multiple time_frames in the inner_frame, then they are stacked horizontally (i.e., left to right)
 - The width of the time_frame is defined by the user as a proportion of the inner_frame width
 - The first time_frame from the left will, typically, be the most detailed (i.e., highest magnification)
 - All time_frames must have the same number of rows 
 - The user can define the number of rows
 - The first part of a task might appear in one time_frame and the second part in a neighbouring time_frame
 - A curtain may start in one time_frame and end in another
 - Time frames are contiguous (i.e., no gaps between them)
 - Time frames cannot overlap

## User Interface Requirements

 - Tabs and fields on data entry window:
   - layout tab (list)
     - top margin
     - right margin
     - bottom margin
     - left margin
     - outer width
     - outer height
     - header height - integer
     - footer height - integer
     - header text - string
     - footer text - string
     - upper scale height - integer
     - lower scale height - integer
     - number of rows - integer
     - horizontal gridlines - yes/no
     - vertical gridlines - yes/no
   - time frames tab (table)
     - start date - date
     - finish date - date
     - width - percentage
     - upper scale intervals - for example, days, weeks, months, years
     - lower scale intervals - for example, days, weeks, months, years
   - tasks tab (table)
     - task id - integer
     - task name - string
     - start date - date
     - finish date - date
     - row number - integer
   - connectors tab (table)
     - from task id - integer
     - to task id - integer
   - swimlanes tab (table)
     - from row number - integer
     - to row number - integer
     - title - string
     - colour - string
   - pipes tab (table)
     - date - date
     - colour - string
   - curtains tab (table)
     - from date - date
     - to date - date
     - colour - string
   - text boxes tab (table)
     - text - string
     - x coordinate - float
     - y coordinate - float
     - colour - string