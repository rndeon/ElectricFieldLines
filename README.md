Electric Field Line Visualizer
===
Interactively displays the electric field lines for a collection of point charges.

Usage:
 1. **Edit Point Charges** mode
    * Mousewheel to choose the value of the point charge to place
    * Left click to place, right click to remove charges
    * Left Click and Drag to move charges around
 2. **Find Field Line** mode
    * Click anywhere to find the field line that runs through that point!
    * Field lines will stop calculating at screen borders, at point charges, and when it hits a zero-field point
 3. **Edit Dielectric Regions** mode
    * Mousewheel to adjust the permittivity of the region your mouse is hovering over
    * Right click to remove a region (it's a bit unintuitive, because I need at least one region to exist, so it'll only agree to delete the region above/to the left of the interface)
    * Left click to add a region (only allows two right now)
 4. **Autostart Lines** button
    * Starts a bunch of field lines at angles around each point charge, if you're over having to click places.
    * The angles at which these start currently set by the `angleresolution` global variable
 5. **Clear Screen** deletes everything placed.

General Notes
---
Runs slower with
- more point charges
- two dielectric regions than with one

but the configurations of them should all be equal.


Runs on Python 3.5 with pygame, and is my first python project. A lot of StackOverflow in this one.