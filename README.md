Electric Field Line Visualizer
===
Interactively displays the electric field lines for a collection of point charges.

Usage:
 1. **Edit Point Charges** mode
    * Mousewheel to choose the value of the point charge to place
    * Left click to place, right click to remove charges
 2. **Find Field Line** mode
    * Click anywhere to find the field line that runs through that point!
    * Field lines will stop calculating at screen borders, at point charges, and when it hits a zero-field point
 3. **Edit Dielectric Regions** button
    * currently does nothing! This is a harder problem than I naively thought when I made this button, and I leave it in to remind me of my hubris
 4. **Autostart Lines** button
    * Starts a bunch of field lines at angles around each point charge, if you're over having to click places.
    * The angles at which these start currently set by the `angleresolution` global variable
 5. **Clear Screen** deletes everything placed.

Runs on Python with pygame, and is my first python project. A lot of StackOverflow in this one.