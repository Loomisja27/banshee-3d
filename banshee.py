import math
from OCC.Core.gp import gp_Pnt, gp_Ax1, gp_Dir, gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
)
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeCylinder,
)
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Union
from OCC.Display.SimpleGui import init_display
from OCC.Core.StlAPI import StlAPI_Writer

# ---------- PARAMETERS ----------
head_radius   = 10.0
body_height   = 40.0
neck_radius   = 6.0
base_radius   = 15.0
wave_amp      = 2.0
wave_freq     = 6
seg_length    = 12.0
arm_radius    = 2.0

color         = (1.0, 1.0, 1.0)
transparency  = 0.5

# ---------- BUILD HEAD ----------
head = BRepPrimAPI_MakeSphere(head_radius).Shape()

# ---------- BUILD BODY WITH WAVY EDGE ----------
profile_sections = []
num_sections = 12
for i in range(num_sections + 1):
    z = (body_height / num_sections) * i
    r = neck_radius + (base_radius - neck_radius) * (i / num_sections)
    if i == num_sections:
        pts = []
        for k in range(64):
            theta = 2 * math.pi * k / 64
            rr = r + wave_amp * math.sin(wave_freq * theta)
            pts.append(gp_Pnt(rr * math.cos(theta), rr * math.sin(theta), z))
        edges = [BRepBuilderAPI_MakeEdge(pts[k], pts[(k+1)%64]).Edge() for k in range(64)]
        wire = BRepBuilderAPI_MakeWire()
        for e in edges: wire.Add(e)
        profile_sections.append(wire.Wire())
    else:
        edge = BRepBuilderAPI_MakeEdge(
            gp_Ax1(gp_Pnt(0,0,z), gp_Dir(0,0,1)),
            r, r, 0, 2*math.pi
        ).Edge()
        wire = BRepBuilderAPI_MakeWire(edge)
        profile_sections.append(wire.Wire())

loft = BRepOffsetAPI_ThruSections(True, False, 1.0e-3)
for w in profile_sections:
    loft.AddWire(w)
body = loft.Shape()

ghost = BRepAlgoAPI_Union(head, body).Shape()

# ---------- BUILD ARMS ----------
def make_arm(x_sign=1):
    upper = BRepPrimAPI_MakeCylinder(arm_radius, seg_length).Shape()
    lower = BRepPrimAPI_MakeCylinder(arm_radius, seg_length).Shape()
    t_sh = gp_Trsf()
    t_sh.SetTranslation(gp_Vec(x_sign*(neck_radius+arm_radius), 0, body_height*0.75))
    upper.Location(t_sh)
    t_el = gp_Trsf()
    t_el.SetTranslation(gp_Vec(x_sign*(neck_radius+arm_radius), seg_length, body_height*0.75))
    lower.Location(t_el)
    return BRepAlgoAPI_Union(upper, lower).Shape()

ghost = BRepAlgoAPI_Union(ghost, make_arm(-1)).Shape()
ghost = BRepAlgoAPI_Union(ghost, make_arm( 1)).Shape()

# ---------- DISPLAY & EXPORT ----------
display, start_display, *_ = init_display()
ais = display.DisplayShape(ghost, update=True, color=color, transparency=transparency)

stl_writer = StlAPI_Writer()
stl_writer.SetASCIIMode(True)
stl_writer.Write(ghost, "banshee.stl")

print("✔ Exported banshee.stl")
start_display()
