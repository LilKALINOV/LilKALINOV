import math

FRAMES = 36


def rotate(point, yaw, pitch):
    x, y, z = point
    cy, sy = math.cos(yaw), math.sin(yaw)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cp, sp = math.cos(pitch), math.sin(pitch)
    y, z = y * cp - z * sp, y * sp + z * cp
    return x, y, z


def project(point, cx, cy, scale, distance=4.2):
    x, y, z = point
    factor = distance / (distance - z)
    return cx + x * scale * factor, cy - y * scale * factor


def icosahedron():
    phi = (1 + 5 ** .5) / 2
    raw = [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
           (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
           (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]
    norm = math.sqrt(1 + phi * phi)
    vertices = [(x / norm, y / norm, z / norm) for x, y, z in raw]
    edges = sorted({tuple(sorted((i, j))) for i in range(12) for j in range(12)
                    if i < j and abs(math.dist(vertices[i], vertices[j]) - 2 / norm) < 1e-6})
    return vertices, edges


def fibonacci_sphere(count):
    points = []
    golden = math.pi * (3 - 5 ** .5)
    for i in range(count):
        y = 1 - 2 * (i + .5) / count
        radius = math.sqrt(1 - y * y)
        points.append((math.cos(golden * i) * radius, y, math.sin(golden * i) * radius))
    return points


def meridian(longitude, steps=28):
    return [(math.cos(lat) * math.sin(longitude), math.sin(lat), math.cos(lat) * math.cos(longitude))
            for lat in (math.pi * (k / steps - .5) for k in range(steps + 1))]


def parallel(latitude, steps=40):
    return [(math.cos(latitude) * math.sin(a), math.sin(latitude), math.cos(latitude) * math.cos(a))
            for a in (2 * math.pi * k / steps for k in range(steps + 1))]


def angles(turns=1.0):
    return [2 * math.pi * turns * f / FRAMES for f in range(FRAMES + 1)]


def depth_opacity(z, near=1.0, far=.12):
    return far + (near - far) * (z + 1) / 2


def animated_edges(vertices, edges, cx, cy, scale, pitch, duration, stroke, width=1.6):
    out = []
    for a, b in edges:
        paths, opacities = [], []
        for yaw in angles():
            pa = rotate(vertices[a], yaw, pitch)
            pb = rotate(vertices[b], yaw, pitch)
            (x1, y1), (x2, y2) = project(pa, cx, cy, scale), project(pb, cx, cy, scale)
            paths.append(f'M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}')
            opacities.append(f'{depth_opacity((pa[2] + pb[2]) / 2):.2f}')
        out.append(f'<path d="{paths[0]}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" fill="none" opacity="{opacities[0]}">'
                   f'<animate attributeName="d" dur="{duration}s" repeatCount="indefinite" values="{";".join(paths)}"/>'
                   f'<animate attributeName="opacity" dur="{duration}s" repeatCount="indefinite" values="{";".join(opacities)}"/></path>')
    return ''.join(out)


def animated_points(points, cx, cy, scale, pitch, duration, fill, radius=2.2, yaw_offset=0.0):
    out = []
    for point in points:
        xs, ys, os_, rs = [], [], [], []
        for yaw in angles():
            p = rotate(point, yaw + yaw_offset, pitch)
            x, y = project(p, cx, cy, scale)
            xs.append(f'{x:.1f}')
            ys.append(f'{y:.1f}')
            os_.append(f'{depth_opacity(p[2], 1, .05):.2f}')
            rs.append(f'{radius * (.6 + .5 * (p[2] + 1) / 2):.2f}')
        out.append(f'<circle cx="{xs[0]}" cy="{ys[0]}" r="{rs[0]}" fill="{fill}" opacity="{os_[0]}">'
                   f'<animate attributeName="cx" dur="{duration}s" repeatCount="indefinite" values="{";".join(xs)}"/>'
                   f'<animate attributeName="cy" dur="{duration}s" repeatCount="indefinite" values="{";".join(ys)}"/>'
                   f'<animate attributeName="r" dur="{duration}s" repeatCount="indefinite" values="{";".join(rs)}"/>'
                   f'<animate attributeName="opacity" dur="{duration}s" repeatCount="indefinite" values="{";".join(os_)}"/></circle>')
    return ''.join(out)


def polyline_frames(points, cx, cy, scale, pitch, turns=1.0):
    frames = []
    for yaw in angles(turns):
        coords = [project(rotate(point, yaw, pitch), cx, cy, scale) for point in points]
        frames.append('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in coords))
    return frames


def static_polyline(points, cx, cy, scale, pitch, yaw=0.0, front_only=True):
    commands, pen_down = [], False
    for point in points:
        p = rotate(point, yaw, pitch)
        x, y = project(p, cx, cy, scale)
        visible = p[2] > -0.05 or not front_only
        if visible:
            commands.append(f'{"L" if pen_down else "M"}{x:.1f} {y:.1f}')
        pen_down = visible
    return ''.join(commands)
