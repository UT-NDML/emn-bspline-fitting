"""
.. module:: operations
    :platform: Unix, Windows
    :synopsis: Provides geometric operations for spline geometry classes

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>
    ** modified by eva_n **

"""

import math
import copy
import warnings
from geomdl import abstract, helpers, linalg, compatibility
from geomdl import _operations as ops
from geomdl.exceptions import GeomdlException
from geomdl._utilities import export


@export
def insert_knot(obj, param, num, **kwargs):
    """ Inserts knots n-times to a spline geometry.

    The following code snippet illustrates the usage of this function:

    .. code-block:: python

        # Insert knot u=0.5 to a curve 2 times
        operations.insert_knot(curve, [0.5], [2])

        # Insert knot v=0.25 to a surface 1 time
        operations.insert_knot(surface, [None, 0.25], [0, 1])

        # Insert knots u=0.75, v=0.25 to a surface 2 and 1 times, respectively
        operations.insert_knot(surface, [0.75, 0.25], [2, 1])

        # Insert knot w=0.5 to a volume 1 time
        operations.insert_knot(volume, [None, None, 0.5], [0, 0, 1])

    Please note that input spline geometry object will always be updated if the knot insertion operation is successful.

    Keyword Arguments:
        * ``check_num``: enables/disables operation validity checks. *Default: True*

    :param obj: spline geometry
    :type obj: abstract.SplineGeometry
    :param param: knot(s) to be inserted in [u, v, w] format
    :type param: list, tuple
    :param num: number of knot insertions in [num_u, num_v, num_w] format
    :type num: list, tuple
    :return: updated spline geometry
    """
    # Get keyword arguments
    check_num = kwargs.get('check_num', True)  # can be set to False when the caller checks number of insertions

    if check_num:
        # Check the validity of number of insertions
        if not isinstance(num, (list, tuple)):
            raise GeomdlException("The number of insertions must be a list or a tuple",
                                  data=dict(num=num))

        if len(num) != obj.pdimension:
            raise GeomdlException("The length of the num array must be equal to the number of parametric dimensions",
                                  data=dict(pdim=obj.pdimension, num_len=len(num)))

        for idx, val in enumerate(num):
            if val < 0:
                raise GeomdlException('Number of insertions must be a positive integer value',
                                      data=dict(idx=idx, num=val))

    # Start curve knot insertion
    if isinstance(obj, abstract.Curve):
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s = helpers.find_multiplicity(param[0], obj.knotvector)

            # Check if it is possible add that many number of knots
            if check_num and num[0] > obj.degree - s:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be inserted " + str(num[0]) + " times",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s))

            # Find knot span
            span = helpers.find_span_linear(obj.degree, obj.knotvector, obj.ctrlpts_size, param[0])

            # Compute new knot vector
            kv_new = helpers.knot_insertion_kv(obj.knotvector, param[0], span, num[0])

            # Compute new control points
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            cpts_tmp = helpers.knot_insertion(obj.degree, obj.knotvector, cpts, param[0],
                                              num=num[0], s=s, span=span)

            # Update curve
            obj.set_ctrlpts(cpts_tmp)
            obj.knotvector = kv_new

    # Start surface knot insertion
    if isinstance(obj, abstract.Surface):
        # u-direction
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s_u = helpers.find_multiplicity(param[0], obj.knotvector_u)

            # Check if it is possible add that many number of knots
            if check_num and num[0] > obj.degree_u - s_u:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be inserted " + str(num[0]) + " times (u-dir)",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s_u))

            # Find knot span
            span_u = helpers.find_span_linear(obj.degree_u, obj.knotvector_u, obj.ctrlpts_size_u, param[0])

            # Compute new knot vector
            kv_u = helpers.knot_insertion_kv(obj.knotvector_u, param[0], span_u, num[0])

            # Get curves_v
            cpts_tmp = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for v in range(obj.ctrlpts_size_v):
                ccu = [cpts[v + (obj.ctrlpts_size_v * u)] for u in range(obj.ctrlpts_size_u)]
                ctrlpts_tmp = helpers.knot_insertion(obj.degree_u, obj.knotvector_u, ccu, param[0],
                                                     num=num[0], s=s_u, span=span_u)
                cpts_tmp += ctrlpts_tmp

            # Update the surface after knot insertion
            obj.set_ctrlpts(compatibility.flip_ctrlpts_u(cpts_tmp, obj.ctrlpts_size_u + num[0], obj.ctrlpts_size_v),
                            obj.ctrlpts_size_u + num[0], obj.ctrlpts_size_v)
            obj.knotvector_u = kv_u

        # v-direction
        if param[1] is not None and num[1] > 0:
            # Find knot multiplicity
            s_v = helpers.find_multiplicity(param[1], obj.knotvector_v)

            # Check if it is possible add that many number of knots
            if check_num and num[1] > obj.degree_v - s_v:
                raise GeomdlException("Knot " + str(param[1]) + " cannot be inserted " + str(num[1]) + " times (v-dir)",
                                      data=dict(knot=param[1], num=num[1], multiplicity=s_v))

            # Find knot span
            span_v = helpers.find_span_linear(obj.degree_v, obj.knotvector_v, obj.ctrlpts_size_v, param[1])

            # Compute new knot vector
            kv_v = helpers.knot_insertion_kv(obj.knotvector_v, param[1], span_v, num[1])

            # Get curves_v
            cpts_tmp = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for u in range(obj.ctrlpts_size_u):
                ccv = [cpts[v + (obj.ctrlpts_size_v * u)] for v in range(obj.ctrlpts_size_v)]
                ctrlpts_tmp = helpers.knot_insertion(obj.degree_v, obj.knotvector_v, ccv, param[1],
                                                     num=num[1], s=s_v, span=span_v)
                cpts_tmp += ctrlpts_tmp

            # Update the surface after knot insertion
            obj.set_ctrlpts(cpts_tmp, obj.ctrlpts_size_u, obj.ctrlpts_size_v + num[1])
            obj.knotvector_v = kv_v

    # Start volume knot insertion
    if isinstance(obj, abstract.Volume):
        # u-direction
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s_u = helpers.find_multiplicity(param[0], obj.knotvector_u)

            # Check if it is possible add that many number of knots
            if check_num and num[0] > obj.degree_u - s_u:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be inserted " + str(num[0]) + " times (u-dir)",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s_u))

            # Find knot span
            span_u = helpers.find_span_linear(obj.degree_u, obj.knotvector_u, obj.ctrlpts_size_u, param[0])

            # Compute new knot vector
            kv_u = helpers.knot_insertion_kv(obj.knotvector_u, param[0], span_u, num[0])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for u in range(obj.ctrlpts_size_u):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_insertion(obj.degree_u, obj.knotvector_u, cpt2d, param[0],
                                                 num=num[0], s=s_u, span=span_u)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(obj.ctrlpts_size_u + num[0]):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = ctrlpts_tmp[u][v + (w * obj.ctrlpts_size_v)]
                        ctrlpts_new.append(temp_pt)

            # Update the volume after knot insertion
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u + num[0], obj.ctrlpts_size_v, obj.ctrlpts_size_w)
            obj.knotvector_u = kv_u

        # v-direction
        if param[1] is not None and num[1] > 0:
            # Find knot multiplicity
            s_v = helpers.find_multiplicity(param[1], obj.knotvector_v)

            # Check if it is possible add that many number of knots
            if check_num and num[1] > obj.degree_v - s_v:
                raise GeomdlException("Knot " + str(param[1]) + " cannot be inserted " + str(num[1]) + " times (v-dir)",
                                      data=dict(knot=param[1], num=num[1], multiplicity=s_v))

            # Find knot span
            span_v = helpers.find_span_linear(obj.degree_v, obj.knotvector_v, obj.ctrlpts_size_v, param[1])

            # Compute new knot vector
            kv_v = helpers.knot_insertion_kv(obj.knotvector_v, param[1], span_v, num[1])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for v in range(obj.ctrlpts_size_v):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for u in range(obj.ctrlpts_size_u):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_insertion(obj.degree_v, obj.knotvector_v, cpt2d, param[1],
                                                 num=num[1], s=s_v, span=span_v)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(obj.ctrlpts_size_u):
                    for v in range(obj.ctrlpts_size_v + num[1]):
                        temp_pt = ctrlpts_tmp[v][u + (w * obj.ctrlpts_size_u)]
                        ctrlpts_new.append(temp_pt)

            # Update the volume after knot insertion
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v + num[1], obj.ctrlpts_size_w)
            obj.knotvector_v = kv_v

        # w-direction
        if param[2] is not None and num[2] > 0:
            # Find knot multiplicity
            s_w = helpers.find_multiplicity(param[2], obj.knotvector_w)

            # Check if it is possible add that many number of knots
            if check_num and num[2] > obj.degree_w - s_w:
                raise GeomdlException("Knot " + str(param[2]) + " cannot be inserted " + str(num[2]) + " times (w-dir)",
                                      data=dict(knot=param[2], num=num[2], multiplicity=s_w))

            # Find knot span
            span_w = helpers.find_span_linear(obj.degree_w, obj.knotvector_w, obj.ctrlpts_size_w, param[2])

            # Compute new knot vector
            kv_w = helpers.knot_insertion_kv(obj.knotvector_w, param[2], span_w, num[2])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for w in range(obj.ctrlpts_size_w):
                temp_surf = [cpts[uv + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)] for uv in
                             range(obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_insertion(obj.degree_w, obj.knotvector_w, cpt2d, param[2],
                                                 num=num[2], s=s_w, span=span_w)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w + num[2]):
                ctrlpts_new += ctrlpts_tmp[w]

            # Update the volume after knot insertion
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v, obj.ctrlpts_size_w + num[2])
            obj.knotvector_w = kv_w

    # Return updated spline geometry
    return obj


@export
def remove_knot(obj, param, num, **kwargs):
    """ Removes knots n-times from a spline geometry.

    The following code snippet illustrates the usage of this function:

    .. code-block:: python

        # Remove knot u=0.5 from a curve 2 times
        operations.remove_knot(curve, [0.5], [2])

        # Remove knot v=0.25 from a surface 1 time
        operations.remove_knot(surface, [None, 0.25], [0, 1])

        # Remove knots u=0.75, v=0.25 from a surface 2 and 1 times, respectively
        operations.remove_knot(surface, [0.75, 0.25], [2, 1])

        # Remove knot w=0.5 from a volume 1 time
        operations.remove_knot(volume, [None, None, 0.5], [0, 0, 1])

    Please note that input spline geometry object will always be updated if the knot removal operation is successful.

    Keyword Arguments:
        * ``check_num``: enables/disables operation validity checks. *Default: True*

    :param obj: spline geometry
    :type obj: abstract.SplineGeometry
    :param param: knot(s) to be removed in [u, v, w] format
    :type param: list, tuple
    :param num: number of knot removals in [num_u, num_v, num_w] format
    :type num: list, tuple
    :return: updated spline geometry
    """
    # Get keyword arguments
    check_num = kwargs.get('check_num', True)  # can be set to False when the caller checks number of removals

    if check_num:
        # Check the validity of number of insertions
        if not isinstance(num, (list, tuple)):
            raise GeomdlException("The number of removals must be a list or a tuple",
                                  data=dict(num=num))

        if len(num) != obj.pdimension:
            raise GeomdlException("The length of the num array must be equal to the number of parametric dimensions",
                                  data=dict(pdim=obj.pdimension, num_len=len(num)))

        for idx, val in enumerate(num):
            if val < 0:
                raise GeomdlException('Number of removals must be a positive integer value',
                                      data=dict(idx=idx, num=val))

    # Start curve knot removal
    if isinstance(obj, abstract.Curve):
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s = helpers.find_multiplicity(param[0], obj.knotvector)

            # It is impossible to remove knots if num > s
            if check_num and num[0] > s:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be removed " + str(num[0]) + " times",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s))

            # Find knot span
            span = helpers.find_span_linear(obj.degree, obj.knotvector, obj.ctrlpts_size, param[0])

            # Compute new control points
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            ctrlpts_new = helpers.knot_removal(obj.degree, obj.knotvector, cpts, param[0], num=num[0], s=s, span=span)

            # Compute new knot vector
            kv_new = helpers.knot_removal_kv(obj.knotvector, span, num[0])

            # Update curve
            obj.set_ctrlpts(ctrlpts_new)
            obj.knotvector = kv_new

    # Start surface knot removal
    if isinstance(obj, abstract.Surface):
        # u-direction
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s_u = helpers.find_multiplicity(param[0], obj.knotvector_u)

            # Check if it is possible add that many number of knots
            if check_num and num[0] > s_u:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be removed " + str(num[0]) + " times (u-dir)",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s_u))

            # Find knot span
            span_u = helpers.find_span_linear(obj.degree_u, obj.knotvector_u, obj.ctrlpts_size_u, param[0])

            # Get curves_v
            ctrlpts_new = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for v in range(obj.ctrlpts_size_v):
                ccu = [cpts[v + (obj.ctrlpts_size_v * u)] for u in range(obj.ctrlpts_size_u)]
                ctrlpts_tmp = helpers.knot_removal(obj.degree_u, obj.knotvector_u, ccu, param[0],
                                                   num=num[0], s=s_u, span=span_u)
                ctrlpts_new += ctrlpts_tmp

            # Compute new knot vector
            kv_u = helpers.knot_removal_kv(obj.knotvector_u, span_u, num[0])

            # Update the surface after knot removal
            obj.set_ctrlpts(compatibility.flip_ctrlpts_u(ctrlpts_new, obj.ctrlpts_size_u - num[0], obj.ctrlpts_size_v),
                            obj.ctrlpts_size_u - num[0], obj.ctrlpts_size_v)
            obj.knotvector_u = kv_u

        # v-direction
        if param[1] is not None and num[1] > 0:
            # Find knot multiplicity
            s_v = helpers.find_multiplicity(param[1], obj.knotvector_v)

            # Check if it is possible add that many number of knots
            if check_num and num[1] > s_v:
                raise GeomdlException("Knot " + str(param[1]) + " cannot be removed " + str(num[1]) + " times (v-dir)",
                                      data=dict(knot=param[1], num=num[1], multiplicity=s_v))

            # Find knot span
            span_v = helpers.find_span_linear(obj.degree_v, obj.knotvector_v, obj.ctrlpts_size_v, param[1])

            # Get curves_v
            ctrlpts_new = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for u in range(obj.ctrlpts_size_u):
                ccv = [cpts[v + (obj.ctrlpts_size_v * u)] for v in range(obj.ctrlpts_size_v)]
                ctrlpts_tmp = helpers.knot_removal(obj.degree_v, obj.knotvector_v, ccv, param[1],
                                                   num=num[1], s=s_v, span=span_v)
                ctrlpts_new += ctrlpts_tmp

            # Compute new knot vector
            kv_v = helpers.knot_removal_kv(obj.knotvector_v, span_v, num[1])

            # Update the surface after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v - num[1])
            obj.knotvector_v = kv_v

    # Start volume knot removal
    if isinstance(obj, abstract.Volume):
        # u-direction
        if param[0] is not None and num[0] > 0:
            # Find knot multiplicity
            s_u = helpers.find_multiplicity(param[0], obj.knotvector_u)

            # Check if it is possible add that many number of knots
            if check_num and num[0] > s_u:
                raise GeomdlException("Knot " + str(param[0]) + " cannot be removed " + str(num[0]) + " times (u-dir)",
                                      data=dict(knot=param[0], num=num[0], multiplicity=s_u))

            # Find knot span
            span_u = helpers.find_span_linear(obj.degree_u, obj.knotvector_u, obj.ctrlpts_size_u, param[0])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for u in range(obj.ctrlpts_size_u):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_removal(obj.degree_u, obj.knotvector_u, cpt2d, param[0],
                                               num=num[0], s=s_u, span=span_u)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(obj.ctrlpts_size_u - num[0]):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = ctrlpts_tmp[u][v + (w * obj.ctrlpts_size_v)]
                        ctrlpts_new.append(temp_pt)

            # Compute new knot vector
            kv_u = helpers.knot_removal_kv(obj.knotvector_u, span_u, num[0])

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u - num[0], obj.ctrlpts_size_v, obj.ctrlpts_size_w)
            obj.knotvector_u = kv_u

        # v-direction
        if param[1] is not None and num[1] > 0:
            # Find knot multiplicity
            s_v = helpers.find_multiplicity(param[1], obj.knotvector_v)

            # Check if it is possible add that many number of knots
            if check_num and num[1] > s_v:
                raise GeomdlException("Knot " + str(param[1]) + " cannot be removed " + str(num[1]) + " times (v-dir)",
                                      data=dict(knot=param[1], num=num[1], multiplicity=s_v))

            # Find knot span
            span_v = helpers.find_span_linear(obj.degree_v, obj.knotvector_v, obj.ctrlpts_size_v, param[1])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for v in range(obj.ctrlpts_size_v):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for u in range(obj.ctrlpts_size_u):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_removal(obj.degree_v, obj.knotvector_v, cpt2d, param[1],
                                               num=num[1], s=s_v, span=span_v)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(obj.ctrlpts_size_u):
                    for v in range(obj.ctrlpts_size_v - num[1]):
                        temp_pt = ctrlpts_tmp[v][u + (w * obj.ctrlpts_size_u)]
                        ctrlpts_new.append(temp_pt)

            # Compute new knot vector
            kv_v = helpers.knot_removal_kv(obj.knotvector_v, span_v, num[1])

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v - num[1], obj.ctrlpts_size_w)
            obj.knotvector_v = kv_v

        # w-direction
        if param[2] is not None and num[2] > 0:
            # Find knot multiplicity
            s_w = helpers.find_multiplicity(param[2], obj.knotvector_w)

            # Check if it is possible add that many number of knots
            if check_num and num[2] > s_w:
                raise GeomdlException("Knot " + str(param[2]) + " cannot be removed " + str(num[2]) + " times (w-dir)",
                                      data=dict(knot=param[2], num=num[2], multiplicity=s_w))

            # Find knot span
            span_w = helpers.find_span_linear(obj.degree_w, obj.knotvector_w, obj.ctrlpts_size_w, param[2])

            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for w in range(obj.ctrlpts_size_w):
                temp_surf = [cpts[uv + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)] for uv in
                             range(obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                cpt2d.append(temp_surf)

            # Compute new control points
            ctrlpts_tmp = helpers.knot_removal(obj.degree_w, obj.knotvector_w, cpt2d, param[2],
                                               num=num[2], s=s_w, span=span_w)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w - num[2]):
                ctrlpts_new += ctrlpts_tmp[w]

            # Compute new knot vector
            kv_w = helpers.knot_removal_kv(obj.knotvector_w, span_w, num[2])

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v, obj.ctrlpts_size_w - num[2])
            obj.knotvector_w = kv_w

    # Return updated spline geometry
    return obj


@export
def refine_knotvector(obj, param, **kwargs):
    """ Refines the knot vector(s) of a spline geometry.

    The following code snippet illustrates the usage of this function:

    .. code-block:: python

        # Refines the knot vector of a curve
        operations.refine_knotvector(curve, [1])

        # Refines the knot vector on the v-direction of a surface
        operations.refine_knotvector(surface, [0, 1])

        # Refines the both knot vectors of a surface
        operations.refine_knotvector(surface, [1, 1])

        # Refines the knot vector on the w-direction of a volume
        operations.refine_knotvector(volume, [0, 0, 1])

    The values of ``param`` argument can be used to set the *knot refinement density*. If *density* is bigger than 1,
    then the algorithm finds the middle knots in each internal knot span to increase the number of knots to be refined.

    **Example**: Let the degree is 2 and the knot vector to be refined is ``[0, 2, 4]`` with the superfluous knots
    from the start and end are removed. Knot vectors with the changing ``density (d)`` value will be:

    * ``d = 1``, knot vector ``[0, 1, 1, 2, 2, 3, 3, 4]``
    * ``d = 2``, knot vector ``[0, 0.5, 0.5, 1, 1, 1.5, 1.5, 2, 2, 2.5, 2.5, 3, 3, 3.5, 3.5, 4]``

    The following code snippet illustrates the usage of knot refinement densities:

    .. code-block:: python

        # Refines the knot vector of a curve with density = 3
        operations.refine_knotvector(curve, [3])

        # Refines the knot vectors of a surface with density for
        # u-dir = 2 and v-dir = 3
        operations.refine_knotvector(surface, [2, 3])

        # Refines only the knot vector on the v-direction of a surface with density = 1
        operations.refine_knotvector(surface, [0, 1])

        # Refines the knot vectors of a volume with density for
        # u-dir = 1, v-dir = 3 and w-dir = 2
        operations.refine_knotvector(volume, [1, 3, 2])

    Please refer to :func:`.helpers.knot_refinement` function for more usage options.

    Keyword Arguments:
        * ``check_num``: enables/disables operation validity checks. *Default: True*

    :param obj: spline geometry
    :type obj: abstract.SplineGeometry
    :param param: parametric dimensions to be refined in [u, v, w] format
    :type param: list, tuple
    :return: updated spline geometry
    """
# TODO: I don't need (surface or) volume knot refinement so maybe I can cut down this function
# TODO: I also need to incorporate the knot_list parameter from helpers
    
    # Get keyword arguments
    check_num = kwargs.get('check_num', True)  # enables/disables input validity checks

    if check_num:
        if not isinstance(param, (list, tuple)):
            raise GeomdlException("Parametric dimensions argument (param) must be a list or a tuple")

        if len(param) != obj.pdimension:
            raise GeomdlException("The length of the param array must be equal to the number of parametric dimensions",
                                  data=dict(pdim=obj.pdimension, param_len=len(param)))

    # Start curve knot refinement
    if isinstance(obj, abstract.Curve):
        if param[0] > 0:    # param is the refinement density in the form [u, v, w] = [#, #, #]
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            new_cpts, new_kv = helpers.knot_refinement(obj.degree, obj.knotvector, cpts, density=param[0])
            obj.set_ctrlpts(new_cpts)
            obj.knotvector = new_kv

    # Start surface knot refinement
    if isinstance(obj, abstract.Surface):
        # u-direction
        if param[0] > 0:
            # Get curves_v
            new_cpts = []
            new_cpts_size = 0
            new_kv = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for v in range(obj.ctrlpts_size_v):
                ccu = [cpts[v + (obj.ctrlpts_size_v * u)] for u in range(obj.ctrlpts_size_u)]
                ptmp, new_kv = helpers.knot_refinement(obj.degree_u, obj.knotvector_u, ccu, density=param[0])
                new_cpts_size = len(ptmp)
                new_cpts += ptmp

            # Update the surface after knot refinement
            obj.set_ctrlpts(compatibility.flip_ctrlpts_u(new_cpts, new_cpts_size, obj.ctrlpts_size_v),
                            new_cpts_size, obj.ctrlpts_size_v)
            obj.knotvector_u = new_kv

        # v-direction
        if param[1] > 0:
            # Get curves_v
            new_cpts = []
            new_cpts_size = 0
            new_kv = []
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts
            for u in range(obj.ctrlpts_size_u):
                ccv = [cpts[v + (obj.ctrlpts_size_v * u)] for v in range(obj.ctrlpts_size_v)]
                ptmp, new_kv = helpers.knot_refinement(obj.degree_v, obj.knotvector_v, ccv, density=param[1])
                new_cpts_size = len(ptmp)
                new_cpts += ptmp

            # Update the surface after knot refinement
            obj.set_ctrlpts(new_cpts, obj.ctrlpts_size_u, new_cpts_size)
            obj.knotvector_v = new_kv

    # Start volume knot refinement
    if isinstance(obj, abstract.Volume):
        # u-direction
        if param[0] > 0:
            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for u in range(obj.ctrlpts_size_u):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Apply knot refinement
            ctrlpts_tmp, kv_new = helpers.knot_refinement(obj.degree_u, obj.knotvector_u, cpt2d, density=param[0])
            new_cpts_size = len(ctrlpts_tmp)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(new_cpts_size):
                    for v in range(obj.ctrlpts_size_v):
                        temp_pt = ctrlpts_tmp[u][v + (w * obj.ctrlpts_size_v)]
                        ctrlpts_new.append(temp_pt)

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, new_cpts_size, obj.ctrlpts_size_v, obj.ctrlpts_size_w)
            obj.knotvector_u = kv_new

        # v-direction
        if param[1] > 0:
            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for v in range(obj.ctrlpts_size_v):
                temp_surf = []
                for w in range(obj.ctrlpts_size_w):
                    for u in range(obj.ctrlpts_size_u):
                        temp_pt = cpts[v + (u * obj.ctrlpts_size_v) + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                        temp_surf.append(temp_pt)
                cpt2d.append(temp_surf)

            # Apply knot refinement
            ctrlpts_tmp, kv_new = helpers.knot_refinement(obj.degree_v, obj.knotvector_v, cpt2d, density=param[1])
            new_cpts_size = len(ctrlpts_tmp)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(obj.ctrlpts_size_w):
                for u in range(obj.ctrlpts_size_u):
                    for v in range(new_cpts_size):
                        temp_pt = ctrlpts_tmp[v][u + (w * obj.ctrlpts_size_u)]
                        ctrlpts_new.append(temp_pt)

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, new_cpts_size, obj.ctrlpts_size_w)
            obj.knotvector_v = kv_new

        # w-direction
        if param[2] > 0:
            # Use Pw if rational
            cpts = obj.ctrlptsw if obj.rational else obj.ctrlpts

            # Construct 2-dimensional structure
            cpt2d = []
            for w in range(obj.ctrlpts_size_w):
                temp_surf = [cpts[uv + (w * obj.ctrlpts_size_u * obj.ctrlpts_size_v)] for uv in
                             range(obj.ctrlpts_size_u * obj.ctrlpts_size_v)]
                cpt2d.append(temp_surf)

            # Apply knot refinement
            ctrlpts_tmp, kv_new = helpers.knot_refinement(obj.degree_w, obj.knotvector_w, cpt2d, density=param[2])
            new_cpts_size = len(ctrlpts_tmp)

            # Flatten to 1-dimensional structure
            ctrlpts_new = []
            for w in range(new_cpts_size):
                ctrlpts_new += ctrlpts_tmp[w]

            # Update the volume after knot removal
            obj.set_ctrlpts(ctrlpts_new, obj.ctrlpts_size_u, obj.ctrlpts_size_v, new_cpts_size)
            obj.knotvector_w = kv_new

    # Return updated spline geometry
    return obj


@export
def find_ctrlpts(obj, u, v=None, **kwargs):
    """ Finds the control points involved in the evaluation of the curve/surface point defined by the input parameter(s).

    :param obj: curve or surface
    :type obj: abstract.Curve or abstract.Surface
    :param u: parameter (for curve), parameter on the u-direction (for surface)
    :type u: float
    :param v: parameter on the v-direction (for surface only)
    :type v: float
    :return: control points; 1-dimensional array for curve, 2-dimensional array for surface
    :rtype: list
    """
    if isinstance(obj, abstract.Curve):
        return ops.find_ctrlpts_curve(u, obj, **kwargs)
    elif isinstance(obj, abstract.Surface):
        if v is None:
            raise GeomdlException("Parameter value for the v-direction must be set for operating on surfaces")
        return ops.find_ctrlpts_surface(u, v, obj, **kwargs)
    else:
        raise GeomdlException("The input must be an instance of abstract.Curve or abstract.Surface")

