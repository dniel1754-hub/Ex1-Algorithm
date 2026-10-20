# Ex1-Algorithm
Implementing a plane projection of 3D volume
Ex1: Algorithm - Implementing a Plane Projection of 3D Volume

Welcome to the repository for Exercise 1 of the Introduction to Software Engineering (OOP/OOD) course.
🎯 Goal

The goal of this assignment is to gain comfort in designing and implementing a complex, under-specified algorithm in a robust, elegant, and runtime-efficient manner. While this is an algorithmic challenge, our primary focus is on software design, architecture, and high code quality.
📐 Problem Statement

Given a 3D raster data matrix ($M$) and a plane ($p$), compute a 2D matrix (image) representing the projection of $p$ onto the volume. Since the problem is not fully specified out-of-the-box, a detailed software design is required.Problem Definition
Input Matrix ($M$): A 3D matrix of size $sx \times sy \times sz$ byte values, where entries $M[x][y][z]$ are unsigned integers (8, 16, or 32 bits).
Dimensions: $1 \le sx, sy, sz < 2^{10}$ and $0 \le x < sx$, $0 \le y < sy$, $0 \le z < sz$.
⚙️ Implementation Requirements
Languages: Implemented in any of the following: Java, Python, C, or C++.
Quality: Code must be correct, stable, and well-designed.
Performance: For a matrix of size $500^3$ bytes, a runtime of at least 100 FPS is expected, with +30 FPS as a hard requirement (e.g., a proper Java implementation achieves 300+ FPS on an M2 Mac 2023).
📂 Data & Resources
Format: NRRD format, utilizing data from the 3D Slicer open-source project.
Sample Data: Start with the recommended 
MRHead_1.nrrd
.
🔬 The Projection Algorithm

A plane is defined by 3 3D points $(a, b, c)$ forming an isosceles triangle where $\text{dist}(a,b) = \text{dist}(a,c)$ (alternatively, an isosceles trapezoid defined by two vectors on the same plane with equal lengths).

For any point $(q)$ within the shape that lies within $M$, project it onto the output 2D matrix $E$:
Let $D_{ab} = \text{dist}(a,b) = \text{dist}(a,c)$ and $D_{bc} = \text{dist}(b,c)$.
Define normalized vectors $v(a,b)$ and $v(a,c)$.
Define an output 2D matrix $E$ of size $D_{ab} \times D_{bc}$.
Step through the plane coordinates iteratively to sample the 3D volume and populate $E$.
✅ To-Do / Checklist

Create repository, define problem statement and project scope in this README.md.

Define the SRS (Software Requirements Specification) document.

Document the main algorithm in detail.

Prepare a dataset of NRRD files.

Define a comprehensive testing strategy (including demo validation).

Implement the project with frequent, meaningful commits.

Implement the demo script (Ex0.py) matching the execution format below.

Conduct experiments, analyze results, and include the output .mp4 file.
🚀 Running the Demo

The project includes a main executable script running in the following format:
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
<file.nrrd>: A 3D volumetric data file in NRRD format.
<file.csv>: A CSV file containing a list of 3 or 4 coordinate points defining the plane.
<file.mp4>: The output video file containing a rendered frame for each corresponding plane coordinate in the CSV file (in sequential order).
