# Project Planning Tool

## Purpose

The purpose of the tool is to enable me, the user, to squeeze as much project-planning related information onto one page as possible.

## Problem

The problems that I have with existing tools include, for example:

 - I can only fit one task per row
 - I cannot change magnification at points on the scale (so I cannot show tasks in distant future at a lower magnification)
 - I cannot be selective about applying (and placing) labels and logic (i.e. connectors)
 - I lack fine control over the dimensions and so it's often hard to get the chart to fit on the desired paper or slide
 - I have to hand draw my charts (using PowerPoint, for example) which is time-consuming and error-prone

## Chart Design

 - outer_frame - control of overall dimensions of inked area; user can apply un-inked margins (i.e. offsets)
 - header_frame - sits at top of outer_frame; contains headers; full width of outer_frame
 - footer_frame - sits at bottom of outer_frame; contains footers; full width of outer_frame
 - header - row within header_frame that contains text; can be stacked
 - footer - row within footer_frame that contains text; can be stacked
 - inner_frame - sits between header_frame and footer_frame; full width of outer_frame
 - chart - sits inside inner_frame; can juxtapose multiple charts at different levels of magnification
 - scale_frame - sits inside a chart; contains scales; full width of chart; typically above row_frame
 - row_frame - sits inside a chart; contains rows; full width of chart; typically below scale_frame
 - scale - sits inside scale_frame; defines a scale for the chart; can stack multiple scales
 - row - sits inside row_frame; defines a row for the chart; stacked vertically
 - swimlane - sits in inner_frame; can be used to group rows visually; full width of inner_frame
 - gridlines - applied to row_frame; can be horizontal, vertical, or both
 - task - multiple tasks can be assigned to a row; a task can appear to cross from one chart to another
 - milestone - assigned to a row
 - connector - line showing flow of logic between tasks and milestones
 - label - user defined text box; associated with a task, milestone, or connector
 - connector - line showing flow of logic between a task and/or milestone
 - text_box - user defined text boxes; can be placed anywhere
 - curtain - user defined time interval; can be placed anywhere inside a row_frame
 - pipe - user defined time point; can be placed anywhere inside a row_frame
 - legend - user can define placement; not sure that we want this feature
 - tasklist - not sure that we want this feature because it requires one task per row
