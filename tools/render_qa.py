"""Render reproducible static QA images without a desktop. Run from any folder."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from renderx.dashboard import Dashboard, SIZE
from renderx.models import make_library
from renderx.scene import Scene
from renderx.camera import Camera
from renderx.learning import LearningState
from renderx.ui import Panel
from renderx.lab import draw_lab, wide_panel
from renderx.obj_loader import load_obj, SAMPLE_OBJ


def main():
    pygame.font.init()
    folder=Path(__file__).resolve().parents[2]/'QA'
    folder.mkdir(exist_ok=True)
    models=make_library(); models['OBJ house']=load_obj(SAMPLE_OBJ)
    cases=[('final-explore','Explore','Cube',0,0),('final-pipeline','Pipeline','Cube',0,0),
           ('final-compare','Compare','Cube',0,0),('final-mesh','Mesh','Torus',0,0),
           ('final-lesson','Lesson','Cube',4,0),('final-clipping','Lesson','Cube',11,0),
           ('final-order','Lesson','Cube',7,0),('final-challenge','Challenge','Cube',0,0),
           ('final-demo','Demo','OBJ house',11,5),('final-obj','Explore','OBJ house',0,0)]
    cases += [('shape-'+name.lower().replace(' ','-'),'Explore',name,0,0)
              for name in ('Sphere','Torus','Cylinder','Cone','Saddle','Ripple','Helix')]
    for name,mode,shape,lesson,demo in cases:
        state=LearningState(mode=mode,lesson_index=lesson,demo_index=demo)
        scene=Scene(shape=shape)
        surface=pygame.Surface((1340 if wide_panel(state) else 1120,740))
        draw_lab(surface,models[shape],scene,Camera(),state,Panel(),0)
        panel=Panel()
        display=pygame.Surface(SIZE)
        Dashboard(panel).draw(display,surface,scene,models,state,Camera())
        pygame.image.save(display,folder/('ui-'+name+'.png'))
    pygame.quit()
    print(f'{len(cases)} current frames saved in {folder}')


if __name__=='__main__': main()
