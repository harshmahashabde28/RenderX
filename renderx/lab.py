"""Compact lesson, mesh, challenge and guided-demo screens and navigation."""
from dataclasses import replace
from math import radians, degrees
import pygame
from renderx import config
from renderx.camera import Camera
from renderx.axes import draw_axes
from renderx.comparison import draw_comparison
from renderx.curriculum import LESSONS, QUESTIONS
from renderx.experiments import clipping_experiment, order_experiment
from renderx.learning import MODES
from renderx.mesh import inspect_mesh
from renderx.pipeline import snapshot_vertex
from renderx.renderer import draw_wireframe, draw_selected_vertex

DEMO_VIEWS = ("Explore", "Explore", "Pipeline", "Compare", "Lesson", "Explore", "Challenge", "Explore")
DEMO_TITLES = ("Choose a shape", "Rotate and transform", "Inspect one vertex",
               "Compare projections", "Clip an edge", "Load an OBJ", "Try a question", "Export the frame")


def wide_panel(learning):
    view = DEMO_VIEWS[learning.demo_index] if learning.mode == "Demo" else learning.mode
    return view in ("Pipeline", "Mesh", "Lesson", "Challenge")


def prepare_lesson(scene, models, learning, load_sample, panel):
    scene.select("Cube")
    scene.angles = (0, 0, 0)
    scene.projection = "Orthographic" if learning.lesson_index == 10 else "Perspective"
    learning.lesson_answer = False
    learning.selected_vertex = 0
    if learning.lesson_index == 7:
        scene.angles = (0, radians(45), 0)
        scene.scale = 1.2
    if learning.lesson_index == 11:
        learning.clip_depth = 0
    if learning.lesson_index == 13:
        panel.notify(load_sample(scene, models))


def prepare_demo(scene, models, learning, controls, panel, load_sample):
    step = learning.demo_index
    if step == 0:
        scene.select("Torus")
    elif step == 1:
        scene.angles = (radians(30), radians(45), radians(20))
    elif step == 2:
        learning.stage_index = 3
    elif step == 3:
        scene.select("Cube")
    elif step == 4:
        learning.lesson_index = 11
        prepare_lesson(scene, models, learning, load_sample, panel)
    elif step == 5:
        panel.notify(load_sample(scene, models))
    elif step == 6:
        learning.challenge.retry()
    elif step == 7:
        controls.screenshot_requested = True


def handle_lab(events, scene, models, learning, controls, panel, previous_mode, load_sample):
    """Old transform keys stay in Controls. New teaching keys are single presses."""
    if not controls.focused:
        return
    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        key = event.key
        shortcuts = {pygame.K_F1+i: mode for i, mode in enumerate(MODES)}
        if key in shortcuts:
            learning.mode = shortcuts[key]
            controls.cancel_drag()
        if key in (pygame.K_n, pygame.K_b):
            names = list(models)
            step = 1 if key == pygame.K_n else -1
            scene.select(names[(names.index(scene.shape)+step) % len(names)])
            controls.cancel_drag()
        if learning.mode == "Lesson":
            if key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET, pygame.K_RETURN, pygame.K_SPACE):
                step = -1 if key == pygame.K_LEFTBRACKET else 1
                learning.lesson_index = (learning.lesson_index+step) % len(LESSONS)
                prepare_lesson(scene, models, learning, load_sample, panel)
            if key == pygame.K_h:
                learning.lesson_answer = not learning.lesson_answer
        elif learning.mode == "Challenge":
            challenge_keys(key, learning.challenge)
        elif learning.mode == "Demo":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHTBRACKET, pygame.K_LEFTBRACKET):
                step = -1 if key == pygame.K_LEFTBRACKET else 1
                new = max(0, min(len(DEMO_VIEWS)-1, learning.demo_index+step))
                if new != learning.demo_index:
                    learning.demo_index = new
                    prepare_demo(scene, models, learning, controls, panel, load_sample)
            if DEMO_VIEWS[learning.demo_index] == "Challenge":
                if key == pygame.K_f:
                    learning.challenge.submit()
                elif key not in (pygame.K_RETURN, pygame.K_SPACE):
                    challenge_keys(key, learning.challenge)
        elif key == pygame.K_h:
            learning.help_visible = not learning.help_visible
        clipping = (learning.mode == "Lesson" and learning.lesson_index == 11) or (
                    learning.mode == "Demo" and learning.demo_index == 4)
        if clipping and key in (pygame.K_u, pygame.K_j):
            learning.clip_depth = max(-2, min(2, learning.clip_depth + (.2 if key == pygame.K_u else -.2)))
    if learning.mode != previous_mode:
        learning.help_visible = False
        controls.cancel_drag()
        if learning.mode == "Lesson":
            prepare_lesson(scene, models, learning, load_sample, panel)
        elif learning.mode == "Demo":
            learning.demo_index = 0
            prepare_demo(scene, models, learning, controls, panel, load_sample)


def challenge_keys(key, challenge):
    if key in (pygame.K_j, pygame.K_k):
        challenge.choose(-1 if key == pygame.K_j else 1)
    elif key in (pygame.K_RETURN, pygame.K_SPACE):
        challenge.submit()
    elif key == pygame.K_h:
        challenge.hint = not challenge.hint
    elif key == pygame.K_t:
        challenge.retry()


def text_lines(surface, font, text, x, y, width=480, color=config.TEXT):
    """Wrap paragraphs for the fixed information panel; return next baseline."""
    line = ""
    for word in str(text).split():
        candidate = (line+" "+word).strip()
        if line and font.size(candidate)[0] > width:
            surface.blit(font.render(line, True, color), (x,y))
            y += 22
            line = word
        else:
            line = candidate
    if line:
        surface.blit(font.render(line, True, color), (x,y))
        y += 22
    return y


def draw_experiment(surface, panel, scene, mesh, learning):
    surface.fill(config.BACKGROUND, (0, 100, config.VIEW_WIDTH, 570))
    if learning.lesson_index == 11:
        a,b,clipped,state,t = clipping_experiment(learning.clip_depth)
        point = lambda p: (300+int(p[2]*100), 410-int(p[0]*90))
        pygame.draw.line(surface, (170,145,227), (310,210), (310,600), 2)
        pygame.draw.line(surface, config.MUTED, point(a), point(b), 4)
        for name,p in (("A",a),("B",b)):
            pygame.draw.circle(surface, config.TEXT, point(p), 6)
            text_lines(surface,panel.normal,f"{name}: z={p[2]:.2f}",point(p)[0]+10,point(p)[1])
        if clipped:
            pygame.draw.line(surface, config.ACCENT, point(clipped[0]), point(clipped[1]), 4)
        text_lines(surface,panel.normal,"SIDE VIEW: Z horizontal / X vertical",24,120,740)
        text_lines(surface,panel.normal,f"Edge: {state.upper()} | U farther / J nearer",24,153,740,config.ACCENT)
        text_lines(surface,panel.small,"Near plane z=0.1",320,220,250)
        text_lines(surface,panel.small,f"A={a}   B={b}",24,620,750)
        if t is not None:
            text_lines(surface,panel.small,f"t={t:.3f}; intersection={tuple(round(v,3) for v in clipped[0])}",24,644,750)
    else:
        point = mesh.vertices[learning.selected_vertex]
        values = order_experiment(point,scene)
        text_lines(surface,panel.normal,"Same vertex and pose; different operation order",24,120,750)
        for i,(title,p) in enumerate(zip(("Scale -> Rotate -> Translate", "Translate -> Rotate -> Scale"), values)):
            cx = 210+i*400
            pygame.draw.line(surface,config.GRID,(cx-160,410),(cx+160,410),2)
            pygame.draw.line(surface,config.GRID,(cx,230),(cx,590),2)
            endpoint = (cx+int(p[0]*12), 410-int(p[2]*12))
            pygame.draw.line(surface,config.ACCENT,(cx,410),endpoint,2)
            pygame.draw.circle(surface,config.SELECTED,endpoint,7)
            text_lines(surface,panel.small,title,cx-175,185,350)
            text_lines(surface,panel.small,str(tuple(round(v,3) for v in p)),cx-175,620,350)
        text_lines(surface,panel.small,"X/Z plots: X right, Z up; 12 pixels/unit. Y is shown numerically.",24,650,750)


def draw_lab(surface, mesh, scene, camera, learning, panel, fps):
    """Draw extra modes; demo reuses the actual existing feature screens."""
    view = DEMO_VIEWS[learning.demo_index] if learning.mode == "Demo" else learning.mode
    display_state = replace(learning, mode=view)
    surface.fill(config.BACKGROUND)
    lesson_camera = Camera((1,0,-1)) if view == "Lesson" and learning.lesson_index == 8 else camera
    snapshots = snapshot_vertex(mesh.vertices[learning.selected_vertex],scene,lesson_camera)
    if view == "Compare":
        draw_comparison(surface,mesh,scene,lesson_camera,display_state,panel.small)
    else:
        draw_wireframe(surface,mesh,scene,lesson_camera)
        if scene.axes_visible:
            draw_axes(surface,lesson_camera,scene.projection,panel.small)
        if view != "Explore" or learning.mode == "Demo":
            draw_selected_vertex(surface,snapshots[-1].coordinates,learning.selected_vertex,panel.normal)
    if view in ("Explore","Pipeline","Compare"):
        panel.draw(surface,scene,mesh,fps,display_state,snapshots if view == "Pipeline" else None)
    else:
        panel.draw_overlay(surface,scene,fps,display_state)
        left = config.VIEW_WIDTH+20
        pygame.draw.rect(surface,config.PANEL,(config.VIEW_WIDTH,0,config.INSPECTOR_WIDTH,config.HEIGHT))
        title = {"Mesh":"Mesh Inspector","Lesson":f"Lesson {learning.lesson_index+1}/{len(LESSONS)}",
                 "Challenge":"Challenge"}[view]
        text_lines(surface,panel.title,title,left,24)
        text_lines(surface,panel.small,scene.shape+" | N/B: next/previous shape",left,70)
        panel.draw_buttons(surface,scene)
        y = 207
        if view == "Mesh":
            report = inspect_mesh(mesh)
            for label,key in (("Vertices","vertices"),("Edges","edges"),("Faces","faces"),
                              ("Minimum XYZ","low"),("Maximum XYZ","high"),("Box center","center"),
                              ("Width / height / depth","size"),("Normalization scale","normalization_scale"),
                              ("Duplicate edges","duplicate_edges"),("Invalid edges","invalid_edges"),
                              ("Disconnected vertices","disconnected")):
                value=report[key]
                if isinstance(value,tuple): value=tuple(round(v,3) for v in value)
                if isinstance(value,float): value=f"{value:.5g}"
                y=text_lines(surface,panel.small,f"{label}: {value}",left,y)+4
            warning="; ".join(report['warnings']) or "No OBJ parsing warnings."
            text_lines(surface,panel.small,warning[:170],left,y,color=config.SELECTED)
        elif view == "Lesson":
            title,explanation,formula,action,question,answer=LESSONS[learning.lesson_index]
            for text,color in ((title,config.ACCENT),(explanation,config.TEXT),(formula,config.SELECTED),
                               (action,config.ACCENT),("Check: "+question,config.TEXT)):
                y=text_lines(surface,panel.small,text,left,y,color=color)+8
            if learning.lesson_answer:
                y=text_lines(surface,panel.small,"Answer: "+answer,left,y,color=config.SELECTED)+6
            for label,point in (("Model",snapshots[0].coordinates),("World",snapshots[5].coordinates),
                                ("Camera",snapshots[6].coordinates)):
                y=text_lines(surface,panel.small,f"v{learning.selected_vertex} {label}: {tuple(round(v,3) for v in point)}",left,y)
            if learning.lesson_index in (7,11):
                draw_experiment(surface,panel,scene,mesh,learning)
        else:
            q=learning.challenge
            y=text_lines(surface,panel.normal,f"Score: {q.score}/{len(QUESTIONS)} | Answered: {len(q.answers)}",left,y)+12
            if q.done:
                y=text_lines(surface,panel.title,"Completed!",left,y)+16
                text_lines(surface,panel.normal,"T: retry the whole question bank.",left,y)
            else:
                question,choices,correct,hint,explanation=QUESTIONS[q.index]
                y=text_lines(surface,panel.normal,f"{q.index+1}. {question}",left,y)+10
                for i,choice in enumerate(choices):
                    color=config.SELECTED if i == q.choice else config.TEXT
                    y=text_lines(surface,panel.normal,("> " if i == q.choice else "  ")+choice,left,y,color=color)+10
                if q.answered:
                    y=text_lines(surface,panel.normal,"Correct!" if q.answers[q.index] else "Incorrect",left,y,color=config.ACCENT)+6
                    text_lines(surface,panel.small,explanation,left,y)
                elif q.hint:
                    text_lines(surface,panel.small,"Hint: "+hint,left,y,color=config.ACCENT)
        angles = ", ".join(f"{degrees(a):.0f}" for a in scene.angles)
        position = ", ".join(f"{v:.2f}" for v in scene.position)
        text_lines(surface,panel.small,f"Angles XYZ: {angles} deg | Scale: {scene.scale:.2f}",left,588)
        text_lines(surface,panel.small,f"Position: ({position})",left,611)
        footer={"Mesh":"Bounds describe model coordinates; N/B changes shape.",
                "Lesson":"[ / ] or Enter: lesson | H: checkpoint answer",
                "Challenge":"J/K: choice | Enter: submit/next | H: hint | T: retry"}[view]
        text_lines(surface,panel.small,footer,left,638)
        text_lines(surface,panel.small,"F1-F7: modes | F12: screenshot | Esc: exit",left,717)
    if learning.mode == "Demo":
        pygame.draw.rect(surface,config.PANEL,(16,16,788,32))
        text_lines(surface,panel.normal,f"DEMO MODE {learning.demo_index+1}/8: {DEMO_TITLES[learning.demo_index]}",24,22,760,config.SELECTED)
        if panel.message and pygame.time.get_ticks() < panel.message_until:
            pygame.draw.rect(surface,config.PANEL,(16,651,788,26))
            text_lines(surface,panel.small,panel.message[:105],24,655,760,config.ACCENT)
        pygame.draw.rect(surface,config.PANEL,(16,679,788,55))
        text_lines(surface,panel.small,"Enter/Space: next step | [: previous | F1: leave demo",24,684,760)
        instruction="J/K: choose; F: submit answer" if learning.demo_index == 6 else "Use normal controls to demonstrate this step."
        text_lines(surface,panel.small,instruction,24,707,760)


def draw_help(surface,panel):
    rectangle=pygame.Rect(70,180,680,410)
    pygame.draw.rect(surface,config.PANEL,rectangle,border_radius=8)
    lines=("RenderX quick help", "F1 Explore | F2 Pipeline | F3 Compare | F4 Mesh",
           "F5 Lessons | F6 Challenge | F7 Guided demo | Tab cycles",
           "N/B next/previous shape | 1/2/3 original shapes | O OBJ",
           "Arrows rotate XY | Q/E rotate Z | WASD pan",
           "Page Up/Down depth | +/- scale | R reset | X axes | P projection",
           ",/. vertex | [/] stage or lesson | V comparison guides",
           "Lessons: H reveals answer | clipping: U/J farther/nearer",
           "Challenge: J/K choice | Enter submit/next | H hint | T retry",
           "Demo: Enter next | [ previous | F submits the challenge",
           "F12 screenshot | Esc exit | H closes this help")
    for i,line in enumerate(lines):
        text_lines(surface,panel.small,line,90,200+i*32,640)
