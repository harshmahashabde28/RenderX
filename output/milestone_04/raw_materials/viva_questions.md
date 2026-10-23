# RenderX — viva questions and short answers

Use these as practice notes. Explain the answers in your own words and be ready to point to the corresponding code or demo.

1. **What is RenderX?**  
   RenderX is a Python desktop graphics application centered on a custom 3D wireframe renderer, with guided challenges and two playable demonstrations.

2. **What is the main purpose of the project?**  
   To make the 3D graphics pipeline observable and interactive: users can manipulate meshes and compare projection and rendering behavior.

3. **What is a wireframe model?**  
   A representation that draws a mesh's edges, making its geometric structure visible without filling its faces.

4. **What is the purpose of a model transform?**  
   It changes an object's scale, orientation, or position before the object is viewed by the camera.

5. **Why does the order of transformations matter?**  
   Matrix operations generally do not commute. Scaling, rotation, and translation in a different order can produce a different result.

6. **What is perspective projection?**  
   It makes distant objects appear smaller by scaling projected coordinates according to depth.

7. **How is orthographic projection different?**  
   It does not shrink objects with distance, which helps compare dimensions without perspective size changes.

8. **Why is near-plane clipping needed?**  
   Perspective division is unsafe at zero depth and unstable near the camera. Clipping limits geometry to the visible camera region before projection.

9. **What is OBJ used for?**  
   OBJ is a text-based interchange format that stores mesh data such as vertex positions and faces. RenderX parses supported geometry into its mesh representation.

10. **Why does RenderX limit OBJ size?**  
    To keep file loading bounded and reject unexpectedly large or complex files before they consume excessive time or memory.

11. **What did the testing suite cover?**  
    Math and mesh logic, UI events, file loading, challenges, maze and shooter state, plus targeted resize, projection-edge, and headless app checks.

12. **What does the SDL dummy video driver mean?**  
    It lets automated runs create a video surface without a normal visible desktop window. It is useful for repeatable tests but cannot verify the real GPU display or system cursor.

13. **Why does Breakpoint use a separate rendering path?**  
    It is a real-time 3D shooter with textured models and shaders, while Explore and Maze emphasize the custom software wireframe pipeline.

14. **What is the main performance result?**  
    In the recorded five-second headless runs, idle Explore averaged about 8.7 ms per frame and the built-in Signal mesh about 23.7 ms. These are not native GPU FPS guarantees.

15. **What is the main limitation of the current validation?**  
    A final interactive Windows check is still needed for native file dialogs, cursor behavior, sound output, and actual OpenGL gameplay.

16. **What changed from the GitHub version?**  
    The project retained the renderer focus and expanded into a new application shell, software rendering modes, challenges, a wireframe maze campaign, and the Breakpoint shooter.

17. **How did you compare versions?**  
    I compared the public GitHub main tree at commit `972266d` with the current local tree at `d34e273`. Since their Git histories are unrelated, I describe the source and feature differences instead of claiming a shared commit-by-commit history.

18. **What would you improve next?**  
    Add a native-machine acceptance checklist, benchmark large but supported OBJ files, improve accessibility and input-device coverage, and keep the project test suite synchronized with documented requirements.
