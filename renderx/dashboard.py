"""Clickable presentation layer. Buttons reuse existing scene and keyboard actions."""
from math import radians, degrees
import pygame
from renderx import config
from renderx.learning import MODES
from renderx.curriculum import LESSONS, QUESTIONS
from renderx.lab import DEMO_VIEWS, DEMO_TITLES, text_lines
from renderx.mesh import inspect_mesh
from renderx.pipeline import snapshot_vertex

SIZE = (1360, 900)
VIEW = pygame.Rect(20, 112, 656, 592)
BG, CARD, BUTTON = (10, 16, 27), (20, 30, 45), (32, 46, 65)


class Dashboard:
    def __init__(self, panel):
        self.panel = panel
        self.buttons = {}
        self.labels = {}
        self.active = set()
        self.hover = None
        self.font = pygame.font.Font(None, 23)
        self.small = pygame.font.Font(None, 20)
        self.title = pygame.font.Font(None, 32)
        self.focused = True

    def button(self, action, label, rect, active=False):
        self.buttons[action] = pygame.Rect(rect)
        self.labels[action] = label
        if active:
            self.active.add(action)

    def layout(self, scene, models, learning):
        self.buttons.clear(); self.labels.clear(); self.active.clear()
        for i, mode in enumerate(MODES):
            self.button(('key', pygame.K_F1+i), f'{mode}  F{i+1}', (20+i*188, 59, 178, 37), mode == learning.mode)
        for i, (label, key) in enumerate((('Save PNG',pygame.K_F12),('Reset',pygame.K_r),('Exit',pygame.K_ESCAPE))):
            self.button(('key',key),label,(992+i*116,13,106,32))
        self.button(('help',), 'Help  ?', (880,13,102,32), learning.help_visible)
        names = list(models)
        if 'OBJ house' not in names:
            names.append('OBJ house')
        for i,name in enumerate(names):
            self.button(('shape',name),name,(716+(i%4)*150,148+(i//4)*34,142,28),scene.shape == name)
        self.button(('key',pygame.K_o),'Load / reload OBJ',(716,289,186,30))
        self.button(('key',pygame.K_p),scene.projection+'  P',(20,714,196,32),True)
        self.button(('key',pygame.K_x),'Axes '+('on' if scene.axes_visible else 'off'),(224,714,124,32),scene.axes_visible)
        self.button(('key',pygame.K_COMMA),'Vertex -',(356,714,98,32))
        self.button(('key',pygame.K_PERIOD),'Vertex +',(462,714,98,32))
        view = DEMO_VIEWS[learning.demo_index] if learning.mode == 'Demo' else learning.mode
        if view == 'Compare':
            self.button(('guides',),'Guides',(568,714,108,32),learning.guides_visible)
        for row,(kind,title) in enumerate((('rotate','Rotate'),('move','Move'))):
            for axis,name in enumerate('XYZ'):
                for sign,symbol in ((-1,'-'),(1,'+')):
                    x=97+axis*194+(0 if sign == -1 else 88)
                    self.button((kind,axis,sign),name+' '+symbol,(x,758+row*40,80,31))
        self.button(('scale',-1),'Smaller -',(97,838,128,31))
        self.button(('scale',1),'Larger +',(233,838,128,31))
        self.button(('key',pygame.K_n),'Next model',(369,838,144,31))
        self.button(('key',pygame.K_b),'Previous',(521,838,144,31))
        if view == 'Pipeline':
            for i in range(8):
                self.button(('stage',i),'',(716,391+i*37,598,33),i == learning.stage_index)
        if view == 'Lesson':
            self.button(('answer',),'Hide answer' if learning.lesson_answer else 'Show answer',(716,769,184,32))
            if learning.lesson_index == 11:
                self.button(('key',pygame.K_j),'Edge nearer',(912,769,190,32))
                self.button(('key',pygame.K_u),'Edge farther',(1114,769,200,32))
        if view == 'Challenge':
            q=learning.challenge
            if not q.done:
                for i,choice in enumerate(QUESTIONS[q.index][1]):
                    self.button(('choice',i),choice,(716,481+i*45,598,37),i == q.choice)
            self.button(('hint',),'Hint',(716,769,134,32),q.hint)
            self.button(('retry',),'Retry',(860,769,134,32))
            self.button(('submit',),'Next question' if q.answered else 'Check answer',(1004,769,310,32))
        if learning.mode in ('Lesson','Demo'):
            self.button(('key',pygame.K_LEFTBRACKET),'Previous '+('step' if learning.mode == 'Demo' else 'lesson'),(716,817,220,36))
            self.button(('key',pygame.K_RIGHTBRACKET),'Next '+('step' if learning.mode == 'Demo' else 'lesson'),(946,817,368,36))
        elif view == 'Pipeline':
            self.button(('stage_step',-1),'Previous stage',(716,817,220,36))
            self.button(('stage_step',1),'Next stage',(946,817,368,36))
        if learning.help_visible:
            # Modal help blocks all covered controls; one obvious close action.
            self.buttons.clear(); self.labels.clear(); self.active.clear()
            self.button(('help',),'Close help',(1050,745,190,38))

    def map_position(self, position):
        if VIEW.collidepoint(position):
            return ((position[0]-VIEW.x)/.8, (position[1]-VIEW.y)/.8)
        return (-100, -100)

    def events(self, events, scene, models, learning, controls):
        """Translate UI clicks into the same commands the existing input layer uses."""
        self.layout(scene,models,learning)
        output=[]
        for event in events:
            if event.type in (pygame.WINDOWFOCUSLOST,pygame.WINDOWMINIMIZED):
                self.focused=False
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self.focused=True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action=next((a for a,r in self.buttons.items() if r.collidepoint(event.pos)),None)
                if action is not None:
                    if not self.focused:
                        continue
                    controls.cancel_drag()
                    kind=action[0]
                    if kind == 'key':
                        output.append(pygame.event.Event(pygame.KEYDOWN,key=action[1]))
                    elif kind == 'shape':
                        if action[1] == 'OBJ house':
                            output.append(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_o))
                        else:
                            scene.select(action[1]); learning.selected_vertex=0
                    elif kind in ('rotate','move'):
                        delta=[0,0,0]; delta[action[1]]=action[2]*(radians(10) if kind == 'rotate' else .2)
                        (scene.rotate if kind == 'rotate' else scene.move)(*delta)
                    elif kind == 'scale': scene.resize(action[1]*.1)
                    elif kind == 'stage': learning.stage_index=action[1]
                    elif kind == 'stage_step': learning.select_stage(action[1])
                    elif kind == 'answer': learning.lesson_answer=not learning.lesson_answer
                    elif kind == 'guides': learning.guides_visible=not learning.guides_visible
                    elif kind == 'help': learning.help_visible=not learning.help_visible
                    elif kind == 'hint': learning.challenge.hint=not learning.challenge.hint
                    elif kind == 'retry': learning.challenge.retry()
                    elif kind == 'submit': learning.challenge.submit()
                    elif kind == 'choice' and not learning.challenge.answered and not learning.challenge.done:
                        learning.challenge.choice=action[1]
                    continue
            if learning.help_visible and event.type in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEMOTION,pygame.MOUSEWHEEL):
                controls.cancel_drag(); continue
            if event.type in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP,pygame.MOUSEMOTION):
                values=event.dict.copy(); values['pos']=self.map_position(event.pos)
                if 'rel' in values: values['rel']=tuple(v/.8 for v in event.rel)
                event=pygame.event.Event(event.type,values)
            output.append(event)
        return output

    def draw(self, target, legacy, scene, models, learning, camera, mouse=(0,0)):
        self.layout(scene,models,learning)
        target.fill(BG)
        for rect in ((12,104,672,608),(696,104,640,773),(12,708,672,169)):
            pygame.draw.rect(target,CARD,rect,border_radius=12)
        def label(text,x,y,font=None,color=config.TEXT):
            target.blit((font or self.font).render(text,True,color),(x,y))
        label('RenderX',20,15,self.title)
        label('LEARNING LABORATORY',146,21,self.small,config.ACCENT)
        label('Choose a model',716,118,self.font)
        label('Click to select. Your original vertices stay unchanged.',904,121,self.small,config.MUTED)
        # Existing renderer keeps its coordinate system; only the displayed viewport scales.
        target.blit(pygame.transform.smoothscale(legacy.subsurface((0,0,820,740)),VIEW.size),VIEW)
        label('Rotate',24,765,self.small,config.MUTED)
        label('Move',24,805,self.small,config.MUTED)
        label('Scale',24,845,self.small,config.MUTED)
        for action,rect in self.buttons.items():
            color=(33,78,78) if action in self.active else BUTTON
            if rect.collidepoint(mouse): color=(47,70,91)
            pygame.draw.rect(target,color,rect,border_radius=7)
            if action in self.active:
                pygame.draw.rect(target,config.ACCENT,rect,1,border_radius=7)
            text=self.small.render(self.labels[action],True,config.TEXT)
            target.blit(text,text.get_rect(center=rect.center))
        view=DEMO_VIEWS[learning.demo_index] if learning.mode == 'Demo' else learning.mode
        mesh=models[scene.shape]
        label(f'{scene.shape}   /   {len(mesh.vertices)} vertices   /   {len(mesh.edges)} edges',914,295,self.small,config.MUTED)
        pygame.draw.line(target,BUTTON,(716,334),(1314,334))
        label(view+' workspace',716,350,self.title)
        if view in ('Pipeline','Compare') and learning.mode != 'Demo':
            label('Coordinates: 820 x 740 render canvas',1010,359,self.small,config.MUTED)
        if learning.mode == 'Demo':
            label(f'DEMO {learning.demo_index+1}/8',1160,354,self.font,config.SELECTED)
        if view == 'Pipeline':
            snapshots=snapshot_vertex(mesh.vertices[learning.selected_vertex],scene,camera)
            for i,stage in enumerate(snapshots):
                label(stage.name,728,400+i*37,self.small)
                coords='Hidden / not projected' if stage.coordinates is None else ', '.join(f'{v:.3g}' for v in stage.coordinates)
                label(coords,1065,400+i*37,self.small,config.SELECTED if i == learning.stage_index else config.TEXT)
            active=snapshots[learning.stage_index]
            y=702
            for line in active.formula:
                label(line,716,y,self.small,config.SELECTED); y+=20
            text_lines(target,self.small,active.explanation,716,y+6,598,config.MUTED)
        elif view == 'Lesson':
            title,explanation,formula,action,question,answer=LESSONS[learning.lesson_index]
            y=text_lines(target,self.font,f'{learning.lesson_index+1}/14  {title}',716,393,598,config.ACCENT)+12
            for text,color in ((explanation,config.TEXT),(formula,config.SELECTED),('Try it: '+action,config.ACCENT),('Checkpoint: '+question,config.TEXT)):
                y=text_lines(target,self.font,text,716,y,598,color)+14
            if learning.lesson_answer:
                y=text_lines(target,self.font,'Answer: '+answer,716,y,598,config.SELECTED)+12
            from renderx.camera import Camera
            lesson_camera=Camera((1,0,-1)) if learning.lesson_index == 8 else camera
            trace=snapshot_vertex(mesh.vertices[learning.selected_vertex],scene,lesson_camera)
            for name,index in (('Model',0),('World',5),('Camera',6)):
                values=', '.join(f'{v:.2f}' for v in trace[index].coordinates)
                y=text_lines(target,self.small,f'v{learning.selected_vertex} {name}: {values}',716,y,598,config.MUTED)
        elif view == 'Challenge':
            q=learning.challenge
            label(f'Score {q.score}/10    Answered {len(q.answers)}/10',716,393,self.font,config.ACCENT)
            if q.done:
                label('Completed! Retry whenever you like.',716,437,self.title)
            else:
                question,choices,correct,hint,explanation=QUESTIONS[q.index]
                text_lines(target,self.font,f'{q.index+1}. {question}',716,420,598)
                if q.answered:
                    label('Correct!' if q.answers[q.index] else 'Not quite - keep learning.',716,627,self.font,config.ACCENT)
                    text_lines(target,self.font,explanation,716,657,598)
                elif q.hint:
                    text_lines(target,self.font,'Hint: '+hint,716,627,598,config.ACCENT)
        elif view == 'Mesh':
            report=inspect_mesh(mesh)
            for i,(name,key) in enumerate((('Vertices','vertices'),('Edges','edges'),('Faces','faces'),('Minimum XYZ','low'),('Maximum XYZ','high'),('Box center','center'),('Width / height / depth','size'),('Normalization','normalization_scale'),('Duplicate edges','duplicate_edges'),('Invalid edges','invalid_edges'),('Disconnected vertices','disconnected'))):
                value=report[key]
                if isinstance(value,tuple): value=tuple(round(v,3) for v in value)
                label(name,716,394+i*29,self.small,config.MUTED)
                label(str(value),1025,394+i*29,self.small)
            text_lines(target,self.small,'; '.join(report['warnings']) or 'Mesh ready. No OBJ parsing warnings.',716,725,598,config.ACCENT)
        else:
            text_lines(target,self.title,'One scene. Two ways to see depth.' if view == 'Compare' else 'Make the maths visible.',716,400,590,config.ACCENT)
            text_lines(target,self.font,'Move Z nearer or farther. Perspective changes size; orthographic keeps the same size while the object stays fully visible.' if view == 'Compare' else 'Choose a shape above, then drag it or use the buttons below the canvas. Open Pipeline to inspect each coordinate calculation.',716,451,590)
            label('LIVE TRANSFORM',716,554,self.small,config.MUTED)
            label('Rotation XYZ   '+', '.join(f'{degrees(v):.0f}°' for v in scene.angles),716,584)
            label('Position XYZ   '+', '.join(f'{v:.2f}' for v in scene.position),716,618)
            label(f'Scale   {scene.scale:.2f}x    |    Selected vertex   {learning.selected_vertex}',716,652)
            text_lines(target,self.font,'Try next: Pipeline > Compare > Lessons > Challenge',716,710,590,config.ACCENT)
            if learning.mode == 'Demo':
                text_lines(target,self.font,DEMO_TITLES[learning.demo_index],716,764,590,config.SELECTED)
        label('Move X: left/right    Y: up/down    Z: nearer/farther',24,882,self.small,config.MUTED)
        pose=' / '.join(f'{v:.1f}' for v in scene.position)
        angles=' / '.join(f'{degrees(v):.0f}' for v in scene.angles)
        label(f'XYZ {pose}   |   Rotation {angles}   |   Scale {scene.scale:.2f}',716,882,self.small,config.MUTED)
        if self.panel.message and pygame.time.get_ticks() < self.panel.message_until:
            pygame.draw.rect(target,(33,65,63),(24,655,648,43),border_radius=7)
            text_lines(target,self.small,self.panel.message,34,661,625,config.TEXT)
        if learning.help_visible:
            shade=pygame.Surface(SIZE,pygame.SRCALPHA); shade.fill((0,0,0,170)); target.blit(shade,(0,0))
            pygame.draw.rect(target,CARD,(100,150,1160,650),border_radius=16)
            label('A quick tour',130,183,self.title,config.ACCENT)
            lines=['1. Choose a mode using the tabs. Choose any model from the shape buttons.',
                   '2. Use Rotate, Move and Scale below the canvas. Dragging and all original keys still work.',
                   '3. Pipeline: click any coordinate row; Vertex - / + changes the inspected point.',
                   '4. Compare: Move Z changes depth in both views. Guides toggles centers and bounds.',
                   '5. Lessons: Previous / Next lesson; Show answer reveals the checkpoint explanation.',
                   '6. Challenge: click an option, Check answer, then Next question. Hint and Retry are available.',
                   '7. Demo: Next step walks through eight examples and saves a screenshot at the end.',
                   'Keyboard: arrows rotate X/Y; Q/E rotate Z; WASD pan; PgUp/PgDn depth; +/- scale.',
                   'F1-F7 modes; N/B shapes; P projection; X axes; O OBJ; R reset; F12 screenshot; Esc exit.',
                   'Mouse: left drag rotates; right drag rotates Z; Shift-left / middle drag pans; wheel scales.']
            for i,line in enumerate(lines): label(line,130,242+i*43,self.font)
            rect=self.buttons[('help',)]; pygame.draw.rect(target,BUTTON,rect,border_radius=7)
            label('Close help',rect.x+47,rect.y+9,self.font)
