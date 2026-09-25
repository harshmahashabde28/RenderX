"""Short lessons and a deterministic, offline multiple-choice question bank."""
from dataclasses import dataclass, field

# title, explanation, formula, action, checkpoint, answer
LESSONS = (
("Vertices and edges", "A vertex is a point. An edge connects two vertex indices.",
 "edge = (vertex_a, vertex_b)", "Use , / . to select a corner; N/B switches shapes.",
 "How many vertices and edges does a cube have?", "8 vertices and 12 edges."),
("Coordinate systems", "Model coordinates describe shape; world coordinates include its pose.",
 "world = rotated_model + position", "Toggle X to see world-direction axes. Move with A/D.",
 "Does moving the object change its original vertices?", "No. Only scene position changes."),
("Scaling", "Uniform scaling multiplies all three coordinates by one factor.",
 "(x,y,z) -> (s*x,s*y,s*z)", "Hold + / - and watch the selected point below.",
 "Scale (1,2,3) by 2.", "(2,4,6)."),
("Translation", "Add position after rotating. Translation changes location, not shape.",
 "(x,y,z) -> (x+tx,y+ty,z+tz)", "Use WASD and Page Up/Down to move in all three axes.",
 "Translate (1,0,0) by (2,3,4).", "(3,3,4)."),
("X rotation", "X stays fixed while Y and Z rotate. Angles use radians internally.",
 "y'=y*cos(a)-z*sin(a); z'=y*sin(a)+z*cos(a)", "Hold Up/Down; compare model and world values.",
 "Rotate (0,1,0) by +90 degrees around X.", "(0,0,1)."),
("Y rotation", "Y stays fixed while X and Z rotate.",
 "x'=x*cos(a)+z*sin(a); z'=-x*sin(a)+z*cos(a)", "Hold Left/Right to rotate around Y.",
 "Rotate (0,0,1) by +90 degrees around Y.", "(1,0,0)."),
("Z rotation", "Z stays fixed while X and Y rotate.",
 "x'=x*cos(a)-y*sin(a); y'=x*sin(a)+y*cos(a)", "Hold Q/E and watch the wireframe turn.",
 "Rotate (1,0,0) by +90 degrees around Z.", "(0,1,0)."),
("Transformation order", "Moving before rotating rotates the position too. The outcomes differ.",
 "S -> Rx -> Ry -> Rz -> T versus T -> Rx -> Ry -> Rz -> S",
 "Use arrows, Q/E, WASD and +/-; compare the two X/Z plots.",
 "Are rotation and translation interchangeable?", "No. In general R(T(p)) differs from T(R(p))."),
("Camera-relative coordinates", "Subtract camera position before projection. This lesson uses camera (1,0,-1).",
 "camera_point = world_point - camera_position", "Move with A/D; compare world and camera rows.",
 "World (2,0,5), camera (1,0,-1): camera point?", "(1,0,6)."),
("Perspective projection", "Dividing by camera depth makes distant geometry look smaller.",
 "sx=cx+f*x/z; sy=cy-f*y/z", "Page Up/Down changes depth. P changes projection.",
 "What happens to a point's center offset when its depth doubles?", "It halves in perspective."),
("Orthographic projection", "Depth does not change size, but near-plane visibility still applies.",
 "sx=cx+k*x; sy=cy-k*y", "Page Up/Down changes depth without scaling the image.",
 "Does orthographic projection divide X by Z?", "No. It multiplies X by a fixed scale."),
("Near-plane clipping", "A crossing edge is shortened, not discarded. Gray is original; green is visible.",
 "t=(near-A.z)/(B.z-A.z); I=A+t*(B-A)", "U moves the edge farther; J moves it nearer. R resets the scene only.",
 "If both endpoints are behind the near plane, what is drawn?", "Nothing. The edge is hidden."),
("Wireframe rendering", "Draw projected edges as 2D lines. Rear edges remain visible.",
 "draw_line(project(clipped_A), project(clipped_B))", "Use N/B to inspect several wireframes; rotate with arrows.",
 "Does Pygame calculate the 3D projection?", "No. RenderX does the maths; Pygame draws 2D lines."),
("OBJ loading", "Positive face indices are 1-based. Polygon boundaries become unique edges.",
 "Python_index = OBJ_index - 1", "O reloads the sample house. N/B returns to built-ins.",
 "Is a quad face connected by four boundary edges or two?", "Four. Shared edges are deduplicated."),
)

# question, choices, correct index, hint, explanation
QUESTIONS = (
("Scale (1,2,3) by 2.", ("(2,4,6)", "(3,4,5)", "(1,2,6)"), 0,
 "Multiply every coordinate.", "Each coordinate is multiplied by the same factor 2."),
("Translate (1,0,0) by (2,3,4).", ("(2,0,0)", "(3,3,4)", "(1,3,4)"), 1,
 "Add corresponding coordinates.", "(1+2,0+3,0+4) = (3,3,4)."),
("Rotate (0,1,0) by +90 degrees about X.", ("(1,0,0)", "(0,0,-1)", "(0,0,1)"), 2,
 "sin(90)=1 and cos(90)=0.", "The X rotation maps positive Y to positive Z."),
("Perspective: double a point's positive depth. Its center offset...",
 ("Doubles", "Halves", "Stays fixed"), 1, "The formula divides by Z.", "f*x/(2*z) is half of f*x/z."),
("Orthographic: move a fully visible model farther away. Its size...",
 ("Stays fixed", "Halves", "Doubles"), 0, "There is no depth division.", "Orthographic uses a constant pixels-per-world-unit scale."),
("Both edge endpoints are behind the near plane. Draw...",
 ("The full edge", "Half the edge", "Nothing"), 2, "Neither endpoint is visible.", "A segment entirely behind the near plane is rejected."),
("OBJ face index 3 refers to which Python index?", ("3", "2", "4"), 1,
 "OBJ starts at 1.", "Subtract one: 3 - 1 = 2."),
("How many edges does a cube have?", ("8", "6", "12"), 2,
 "Four on each square plus four connectors.", "4 + 4 + 4 = 12; 8 is its vertex count."),
("Why can Translate -> Rotate differ from Rotate -> Translate?",
 ("The first also rotates the position", "Only one uses radians", "They are always equal"), 0,
 "Think about an orbit around the origin.", "Rotating after translation rotates the translation vector as well."),
("Near=0.1, A.z=-0.9, B.z=1.1. Intersection t?", ("0.1", "0.5", "1.0"), 1,
 "t=(near-A.z)/(B.z-A.z).", "(0.1+0.9)/(1.1+0.9) = 1/2."),
)


@dataclass
class Challenge:
    index: int = 0
    choice: int = 0
    answers: list = field(default_factory=list)
    hint: bool = False

    @property
    def done(self):
        return self.index == len(QUESTIONS)

    @property
    def score(self):
        return sum(self.answers)

    @property
    def answered(self):
        return len(self.answers) > self.index

    def choose(self, step):
        if not self.done and not self.answered:
            self.choice = (self.choice+step) % len(QUESTIONS[self.index][1])

    def submit(self):
        if self.done:
            return
        if self.answered:
            self.index += 1
            self.choice = 0
            self.hint = False
        else:
            self.answers.append(self.choice == QUESTIONS[self.index][2])

    def retry(self):
        self.index = self.choice = 0
        self.answers.clear()
        self.hint = False
