# Ex1: Project Explanation - 3D Volume Projection onto a Plane

Nov 7, 2026
@Nitay Caspi

## In Brief

Imagine an MRI scan of a head. The scanner doesn't save a single image, but rather a 3D "cube" of numbers: for every point inside the head, there is a number indicating its brightness. To see something on a screen, we need to "cut" this cube with some surface, much like slicing a loaf of bread and looking at the slice.

This is exactly what our program does. It takes two things:

1. A cube of numbers (NRRD file), for example, the head scan.

2. A list of slices (CSV file). Each slice is described by a triangle or a trapezoid placed somewhere inside the cube, at any angle.

It outputs a video (MP4 file). Each frame in the video is the image seen on the corresponding triangle or trapezoid, in the same order as the rows in the list. When the slice is moved slightly from row to row, the video shows how the slice "passes" through the head.

**Where it stands:** Everything is implemented, tested, and documented. All 87 automated tests pass (4 dataset-volume tests skip only if the optional NRRD files have not been downloaded into `data/`).

This document explains from the beginning what we built and why, without assuming prior knowledge. It can be read top to bottom: each section relies only on what has already been explained before it.

## Basic Concepts

It's worth going over these concepts first, as they appear throughout the document.

| Concept | Simple Explanation | 
| ----- | ----- | 
| Volume ($M$) | A 3D array of numbers, like a Lego cube. For example, $256 \times 256 \times 130$: $256$ in width, $256$ in height, and $130$ in depth. | 
| Voxel | A single cube inside the volume. This is a "3D pixel". Every voxel has an address $(i, j, k)$ and one numerical value. | 
| Pixel | A single square in a 2D image, with an address (row, column). | 
| NRRD | A common file format in medical imaging for saving volumes. It has a header (size, number type) followed by the data itself. | 
| Value type (`uint8`, `uint16`, `uint32`, `int16`) | How much memory each number takes. `uint8` is up to $255$, `uint16` is up to $65,535$, `uint32` is up to about 4 billion. `int16` also allows negative numbers. | 
| Plane / Slice | A flat surface passing through the volume. For us, it is always a triangle or a trapezoid. | 
| Isosceles Triangle | A triangle where two sides (legs) are the same length. The vertex between them is called $a$, and the third side is the base, $b-c$. | 
| Isosceles Trapezoid | A quadrilateral with two parallel bases (short and long) and two equal legs. A rectangle is a special case. | 
| Projection ($E$) | The 2D image obtained from one slice. This is the output of the algorithm. | 
| CSV | A text file of a table, with comma-separated values. It can be opened in Excel. | 
| MP4 & H.264 | A standard video format, and its compression method. The compression is "lossy": the image in the video is almost identical to the source, but not exactly. | 
| FPS | Frames per second. For us, this has two different meanings, see the experiment results. | 
| EPS | Error tolerance, $0.001$. A computer does not calculate fractions with perfect precision, so two lengths are considered "equal" if the difference between them is between $-0.001$ and $0.001$. | 
| Branch & PR | A branch is a separate working copy of the code in Git. A PR (Pull Request) is a request to merge a branch into the main branch, which the partner sees and approves before it goes in. | 

## The Assignment

This is Assignment 1 in the "Introduction to Software Engineering" course. The lecturer partially defined an algorithm, and we need to implement it in a robust way (so it doesn't crash on bad input), fast, and well-designed. The grade does not solely depend on the algorithm working: the code structure, documents, and tests are also evaluated.

## What Goes In and What Comes Out

|  | What is it | Example | 
| ----- | ----- | ----- | 
| **Input 1: Volume** | An `.nrrd` file with up to $1023$ voxels in each axis, with $8$, $16$, or $32$-bit numbers. | `MRHead_1.nrrd`, a head scan sized $256 \times 256 \times 130$ | 
| **Input 2: Slice List** | A `.csv` file. Each row is one slice. | `head.csv`, with 280 rows | 
| **Output** | An `.mp4` file. One frame for each row in the CSV, in the same order. | `out.mp4`, with 280 frames | 

The program is run like this:
`python Ex0.py <file.nrrd> <file.csv> <file.mp4>`

Meaning: the volume file name, the slices file name, and the output video file name. We also added an optional flag that determines how fast the video plays. Without it, the video plays at $10$ frames per second (`--fps 10`).

### The Speed Requirement

On a volume of $500 \times 500 \times 500$ ($125$ million voxels), the program must calculate at least $30$ images per second, and the goal is $100$. We only measure the calculation time of the image itself, excluding the time to read the file from the disk and the time to generate the video. This is the hardest requirement in the assignment, and it dictated most of our decisions.

### What Does the CSV File Look Like?

This is the format published by the lecturer, and these are the first two rows from his example:
`Number of Points (3 or 4), x1, y1, z1, x2, y2, z2, x3,y3, z3, x4, y4, z4`
`3,200,200,0,0, 200, 400, 400, 200, 400,,,`
`4,200,0,0,200,0,500, 200, 400,0, 200, 400, 500`

* The first row is a header, and the program skips it.

* The first number in each row indicates how many points there are: $3$ for a triangle, $4$ for a trapezoid.

* The points follow, three numbers ($x, y, z$) for each point. For a triangle, the columns for the fourth point are empty.

* Empty rows and rows starting with `#` are comments, and the program skips them.

* **The order of the points.** In a triangle, the order is: first the vertex ($a$) between the two legs, followed by the two ends of the base ($b, c$). In a trapezoid, the order is: one leg from $a1$ to $b$, followed by the second leg from $a2$ to $c$. The short base is $a1-a2$ and the long one is $b-c$.

Although the Q&A section names the four vertices as $(a1, a2, b, c)$ when stating the geometric rules, we deduced the CSV column order from the lecturer's sample CSV: only in leg order $(a1, b, a2, c)$ does his row 4 result in a valid trapezoid. We documented this decision in `ADR-0001`.

## The Algorithm

**The core idea: Start from the image, not the volume.**

There are two ways to calculate a slice image:

* **The naive way:** Go over all voxels in the volume, and check for each one if it touches the triangle. In a $500^3$ volume, that's $125$ million checks per image, mostly redundant, because the triangle touches very few voxels. This is too slow.

* **Our way, "backward mapping":** Start from the empty output image. For each pixel in it, ask: "Which point on the triangle do you represent?", calculate that point in space, and read the value from the volume only there. The work is proportional to the number of pixels in the image (about $200$ thousand in the lecturer's triangle), and not to the volume size.

This is like paint-by-numbers: you don't search the entire paint box to find where to put each color; instead, you go over the squares one by one and check which color belongs to each.

### Step 0: Check if the Shape is Valid

Before calculating anything, check that the row in the CSV actually describes a valid isosceles triangle or trapezoid. The rules (with EPS tolerance of $0.001$):

* The legs are equal in length. This is the definition of "isosceles".

* The sides are not zero length, and the vertex of a triangle is not on the base line (otherwise it's a line, not a triangle).

* In a trapezoid: all four points are on the same plane. Four arbitrary points in space do not necessarily lie on one flat surface.

* In a trapezoid: the top base is not longer than the bottom base, and the legs do not intersect (otherwise you get a "butterfly" shape).

* No side is longer than $3544$ voxels, twice the diagonal of the largest permitted volume. This ensures a bad row won't generate a massive image that crashes the computer.

A row that fails one of the rules does not crash the program. A warning is printed with the row number and the reason, and a marked error frame (a black canvas with a diagonal cross `X` and `ERR <frame>`) is written instead.

### Step 1: A Triangle is a Trapezoid with a Top Base of Length Zero

To avoid writing two algorithms, we treat a triangle as a trapezoid where its two top vertices are at the same point: $a1 = a2 = a$. From now on, there are always four points, and two legs: from $a1$ to $b$ and from $a2$ to $c$.

### Step 2: Image Size

Every pixel in the image represents a step of one voxel in space. Therefore:

* The number of rows $H$ is determined by the leg length: $H = [\text{leg length}] + 1$.

* The number of columns $W$ is determined by the long base length: $W = [\text{long base length}] + 1$.

The symbol $[]$ means rounding down. We add $1$ so that both the top edge and the bottom edge fit into the image: a line of length $10$ units contains $11$ points ($0, 1, ..., 10$).

### Step 3: Go Row by Row

Row $0$ in the image is the top edge of the shape (the vertex, for a triangle), and the last row is the base. For every $y$ row, we advance $y$ steps of length $1$ along each leg, getting two points:

* The point on the left leg: $a1(y)$.

* The point on the right leg: $a2(y)$.

The segment between them is the "row" of the shape at this height. In a triangle, the segment starts as a single point at row $0$ and gradually widens until it reaches the base length at the last row.

### Step 4: Go Column by Column

The image width is always $W$, but different rows have different widths. Therefore, we center each row in the middle of the image, so a triangle looks like a triangle standing on its base in the image.

For each column, we calculate how far it is from the left edge of the row. If the column falls *inside* the row, we travel that same distance along the row in space, getting a 3D point. If it's outside the row, the pixel is black.

A pixel is considered "inside" even if it exceeds the row edge by up to half a pixel. Without this margin, a row narrower than one pixel (like the vertex) could fall between two columns and disappear. This way, every row gets at least one pixel.

### Step 5: Read the Value from the Volume

The point we calculated usually has fractions, e.g., $(89.44, 200, 200)$, but the volume only has voxels at whole addresses. Therefore, we round to the nearest voxel, $(89, 200, 200)$, and take its value. This is the "nearest neighbor" method, which is the fastest and doesn't invent values that don't exist in the data.

If the resulting voxel is outside the volume (e.g., a negative coordinate), the pixel gets $0$, meaning black. This is not an error: a slice is allowed to protrude from the volume.

### Full Numerical Example

Let's take the first row from the lecturer's example: `3,200,200,0,0, 200, 400, 400, 200, 400`. This is a triangle with:

* Vertex $a = (200, 200, 0)$

* Base ends $b = (0, 200, 400)$ and $c = (400, 200, 400)$

Meaning the triangle stands upright in the middle of the volume. All points have $y=200$.

1. **Validity.** Both legs are of length $\sqrt{200^2 + 400^2} \approx 447.21$. They are equal, so the triangle is valid. The base is of length $400$.

2. **Image size.** $H = 447 + 1 = 448$ rows, and $W = 400 + 1 = 401$ columns.

3. **Step direction.** One step on the left leg moves by $(-0.894, 0, 0.447)$, and on the right by $(0.894, 0, 0.447)$. Every step moves a distance of $1$ from the vertex.

4. **Row 100.** After $100$ steps: $a1(100) = (110.56, 200, 89.44)$ and $a2(100) = (289.44, 200, 89.44)$. The row width is $178.88$, and it's centered in the image, so it starts at column $200 - 89.44 = 110.56$.

5. **Column 200 at row 100.** It is $89.44$ away from the beginning of the row, meaning inside the row. The point in space is $(200, 200, 89.44)$, rounded to $(200, 200, 89)$. Therefore, the pixel at row $100$, column $200$, gets the value of the voxel $M[200, 200, 89]$.

6. **Column 100 at row 100.** It is $10.56$ columns before the start of the row, outside the triangle, and therefore the pixel is black.

We do this for all $\approx 180,000$ ($401 \times 448$) pixels, obtaining an image of a triangle with what is seen inside it, and black around it.

### Two Deviations from the Course's Pseudo-code

The lecturer provided pseudo-code (an algorithm description in words and simplified code). We found two issues in it and fixed them. It's worth understanding them because an evaluator might ask why our code is different:

1. **The pseudo-code skips the first row.** It advances the points one step forward *before* sampling, so the vertex itself disappears from the image. In our code, we sample first and advance later, so both the top edge and the base are included.

2. **The pseudo-code might leave holes in the image.** It walks along the row in space and calculates *to which column* to write. The column ends up being a number with a fraction (e.g., $155.28$), and rounding it can skip a column or write to the same column twice. In our approach, the direction is reversed: we go over each whole column and calculate its point, so each pixel is calculated exactly once.

All precise formulas are located in `ALGORITHM.md`.

## Code Structure

### Why Divide the Code into Parts

We could have written the entire program in one long file. It would work, but it would be hard to understand, hard to test, and hard to change. The course focuses on Object-Oriented Programming (OOP), so we divided the code into classes. A class is a "component" with one clear role. Every class knows how to do one thing, and can be tested alone.

The rule guiding us: each component has one reason to change. For example, if tomorrow we want to save GIFs instead of MP4s, we will only change `VideoWriter`, and nothing in the algorithm will be affected.

### What Happens When You Run the Program

1. `Ex0.py` reads the file names from the command line and checks that they exist.

2. `Volume` loads the NRRD file into memory and finds the smallest and largest values in the volume.

3. `PlaneReader` reads the CSV file. For each row, it returns either a valid triangle/trapezoid, or an error message with the row number.

4. A warning is printed for every invalid row.

5. **For each row in order:** `Projector` calculates the slice image. `FrameComposer` turns it into a frame that can be placed in a video, and `VideoWriter` writes the frame. An invalid row gets a marked error frame (`composer.error_frame(r.frame)`).

6. Finally, a summary is printed: how many frames were written, how many are error frames, and how fast the calculation ran.

### The Files

| File | Class | What it does | 
| ----- | ----- | ----- | 
| `Ex0.py` |  | The entry point. Connects all the parts (the steps above), prints warnings and errors, and returns an exit code: $0$ for success, $1$ for failure, $2$ for bad command syntax. | 
| `projection/volume.py` | `Volume` | Loads the volume. Saves it as a `data[x, y, z]` array and calculates the minimum and maximum values. | 
| `projection/plane_reader.py` | `PlaneReader` | Handles CSV reading. Deals with headers, comments, and broken rows. | 
| `projection/geometry.py` | `TrianglePlane`, `TrapezoidPlane` | Represents a triangle or a trapezoid, and checks all validity rules from step 0 of the algorithm. | 
| `projection/projector.py`, `_kernel.py` | `NumbaProjector`, `NumpyProjector` | The algorithm itself: receives a volume and a plane, and returns the image $E$. There are two versions (see below). | 
| `projection/frame_composer.py` | `FrameComposer` | Prepares a frame for the video, including marked error frames (details below). | 
| `projection/video_writer.py` | `VideoWriter` | Writes the frames to the MP4 file. | 
| `tests/` |  | The automated tests. | 
| `benchmarks/bench_projection.py` |  | A script that measures how many images per second the algorithm calculates. | 

### What `FrameComposer` Does and Why We Need It

Two small issues separate a "slice image" from a "video frame":

* **Brightness.** In a video, every pixel is a number between $0$ (black) and $255$ (white), but in a volume, values can reach millions. Therefore, we convert each value relative to the range of the *entire* volume: the minimum becomes $0$ and the maximum becomes $255$. We use the same range for the whole video, otherwise the brightness would "jump" from frame to frame.

* **Size.** Every slice yields a different sized image, but all frames in a video must be the exact same size. Therefore, we calculate the maximum size of all images in advance, and place each image in the center of a black "canvas" of that size, without stretching it. Dimensions are rounded to an even number, as the video format requires.

### Why Are There Two Versions of the Algorithm?

Regular Python is very slow with loops over hundreds of thousands of pixels. Thus, we used a library that accelerates the calculation:

* `NumbaProjector` (default). Numba translates the loop into machine code, just like in C, and runs different rows of the image in parallel on all CPU cores. The first time takes a few seconds to compile, and then it is extremely fast.

* `NumpyProjector` (fallback). NumPy performs the same calculations on entire arrays at once. It is slower (FPS drops below 30 on large diagonal planes), and is used only when Numba is not installed.

Both versions do exactly the same calculations in the same order, and tests ensure they output a bit-for-bit identical image to a simple reference loop, pixel by pixel. This decision is documented in `ADR-0004`.

### An Invalid Row Does Not Stop the Run

We considered two options: skip an invalid row, or write an error frame in its position. We chose a marked error frame (a black canvas with a diagonal cross `X` and `ERR <frame>`), because that way frame number $X$ always corresponds to row number $X$ in the CSV, and the viewer can immediately distinguish an invalid row from a valid slice that lies outside the volume. This decision is documented in `ADR-0002` and `ADR-0005`.

## Tests

### What is an Automated Test?

An automated test is a small function that runs a piece of code on a known input and verifies that the result is what we expected. For example: "take row 3 from the lecturer's example, and make sure it is marked as invalid, because its legs are of length $497.39$ and $476.86$".
The advantage: after every code change, we run a single command `python -m pytest`, and in less than half a minute we know we didn't break anything. We have 87 tests, and they all pass.

### What is Tested?

| Test File | Number | What is tested, in simple words | 
| ----- | ----- | ----- | 
| `test_projector.py` | 26 | That the image obtained from each type of slice is correct: straight and diagonal slices, a slice leaving the volume, a triangle's vertex, and all number types. Each test runs on both versions of the algorithm. | 
| `test_geometry.py` | 19 | That validity rules work: valid rows pass, broken rows are rejected with the correct reason. | 
| `test_dataset.py` | 13 | That all class volumes load, and that the edge-case file from a classmate gives the exact results expected. | 
| `test_volume_and_cli.py` | 12 | Full run from NRRD file to video, command errors (missing file, non-existent folder), and the `--fps` flag. | 
| `test_plane_reader.py` | 11 | CSV reading: header, comments, empty rows, incorrect column count, and text instead of numbers. | 
| `test_frame_composer.py` | 6 | Brightness conversion to $0-255$, placing the image on the canvas, and rendering marked error frames. | 

### The "Encoded Volume" Trick

How do you test that a slice image is correct without looking at it? We built a synthetic volume where the value of every voxel encodes its address: the value at $(i, j, k)$ is $i + 64 \cdot j + 4096 \cdot k$. This way, from any pixel in the image, you can reconstruct exactly which voxel it was taken from, and verify it's the right one.

Additionally, we wrote a third, simple, and slow version of the algorithm: a standard loop over every pixel that is easy to read and compare to the document. Tests ensure both fast versions give the exact same output as the simple version.

### Manually Conducted Tests

Three things we tested outside of `pytest`:

* **Speed (TC-44):** The script `bench_projection.py` measures how many images per second the algorithm calculates.

* **Comparison against class data (TC-45):** We compared our frames to the images that came with the class data.

* **Playback (TC-46):** We opened the videos in a standard video player.

## Design Documents

In the Design Docs lecture, the lecturer presented a chain of documents that every orderly software project needs. Every document answers one question, and they build upon each other:

1. **`SRS.md`**: What should the system do? The requirements list. Functional requirements (`FR-1...FR-7`, e.g., "The software reads NRRD") and non-functional requirements (`NFR-1...NFR-4`, e.g., "At least 30 FPS"). It also includes a Use Case (`UC-01`): a step-by-step description of what happens when a user runs the software, including what happens when something goes wrong.

2. **`SDD.md`**: How is the system built? The components, classes, and their relationships, with diagrams (in Mermaid, a language GitHub turns into diagrams).

3. **`ALGORITHM.md`**: How is the core component built? The algorithm in full detail, with formulas and speed measurements.

4. **`TESTING.md`**: How do we prove it works? The test plan, and a list of all test cases: `TC-01...TC-48`. Input, expected result, and which requirement each test proves.

5. **Traceability Table**: At the end of `SRS.md`, it connects the whole chain: for each requirement, you can see in which code file it is implemented, which test tests it, and if it passes. This proves no requirement was forgotten.

Two more things in the repo:

* **`docs/adr/`**: Five ADR (Architecture Decision Record) documents. Each is a short page documenting one decision: what was the problem, what options were considered, what we chose, and why. They cover: point order in CSV (0001), invalid rows and marked error frames (0002, superseded by 0005), working with voxel indices instead of millimeters (0003), and using Numba (0004).

* **`AGENTS.md`**: Instructions for AI tools (like Copilot, Claude) that write code, so they work according to the project's rules: which commands to run, what is forbidden to change, and when a task is considered done. The lecturer talked about AI development with agents, and this is the standard file for it.

## Experiment Results

### First: Two Types of FPS

The term FPS (Frames Per Second) appears in two places for us, and it's easy to confuse them:

* **Projection FPS:** How many slice images the program manages to calculate in a second. This is the algorithm's speed, and the assignment places a requirement on it ($30$ minimum, $100$ target).

* **Video FPS:** How fast the video plays when opened. This is just a matter of viewing comfort, and is set with the `--fps` flag. A 120-frame video lasts 12 seconds at 10 FPS, and 4 seconds at 30 FPS. The frames themselves are identical.

### Speed on a Synthetic Volume

The script `bench_projection.py` builds a random $500 \times 500 \times 500$ volume and measures how many images per second are produced for five different slices. We achieved an FPS between $453-3942$ with Numba across benchmark runs, depending on the slice. The slowest is a large diagonal slice, because it has the most pixels, and its voxels are scattered in memory. Even the slowest is far above the 100 FPS target. Without Numba, using only NumPy, the slowest drops near or below the 30 FPS minimum.

### On Real Volumes from Class

A student from the class shared a folder with several volumes and a CSV file for each. We ran each volume with its CSV. The videos are saved in the `experiment/` folder, and each video has a preview image in `experiment/previews/` to quickly see what's in it. The videos were created at 30 FPS.

| Volume | What it is | Size, Value type | Slices File | Frames | Projection FPS | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| `MRHead_1` | Head MRI scan | $256 \times 256 \times 130$, `int16` | `head.csv` | 280 | 428 | 
| `biscuit_cake` | Biscuit cake | $256 \times 256 \times 130$, `uint16` | `biscuit_cake.csv` | 120 | 320 | 
| `croissant` | Croissant | $500 \times 500 \times 500$, `uint8` | `croissant.csv` | 100 | 299 | 
| `croissant` | Croissant, with lecturer's example | $500 \times 500 \times 500$, `uint8` | `lecturer_example.csv` | 4 (one error frame) | 490 | 
| `onion` | Onion | $256 \times 256 \times 130$, `uint8` | `onion.csv` | 120 | 1312 | 
| `swiss_roll` | Swiss roll | $256 \times 256 \times 130$, `uint32` | `swiss_roll.csv` | 120 | 823 | 
