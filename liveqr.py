#!/bin/env python

import qrdetect
import cv2
import numpy as np
from pyzbar.pyzbar import decode as read_qr
def make_picture(picture):
    orig_img = cv2.imread(picture)
    big_quads, small_quads = qrdetect.get_quads(orig_img)
    #big_quads, small_quads = [[169, 213, 370, 522], [426, 265, 543, 406], [639, 248, 712, 321], [748, 218, 824, 438], [865, 168, 1008, 635]], [[170, 214, 258, 324], [313, 236, 368, 321], [173, 402, 258, 518]]
    if big_quads == [] or small_quads == []:
        return -1, ["No codes found"]
    text = {}
    def group_quads(big_quads, small_quads):
        groups = {}
        for q in small_quads:
            for i in range(len(big_quads)):
                b = big_quads[i]
                if b[0] <= (q[0] + q[2]) / 2 <= b[2] and b[1] <= (q[1] + q[3]) / 2 <= b[3]:
                    if not i in groups:
                        groups[i] = []
                    groups[i].append(q)
        return groups
    def sort_quads(groups):
        for i in groups:
            group = []
            g = groups[i]
            if len(g) < 3:
                continue
            mid0 = (g[0][0]+g[1][0]+g[2][0])//3
            mid1 = (g[0][1]+g[1][1]+g[2][1])//3
            if g[0][0] < mid0 and g[0][1] < mid1:
                group.append(g[0])
            if g[1][0] < mid0 and g[1][1] < mid1:
                group.append(g[1])
            if g[2][0] < mid0 and g[2][1] < mid1:
                group.append(g[2])
            if g[0][0] > mid0 and g[0][1] < mid1:
                group.append(g[0])
            if g[1][0] > mid0 and g[1][1] < mid1:
                group.append(g[1])
            if g[2][0] > mid0 and g[2][1] < mid1:
                group.append(g[2])
            if g[0][0] < mid0 and g[0][1] > mid1:
                group.append(g[0])
            if g[1][0] < mid0 and g[1][1] > mid1:
                group.append(g[1])
            if g[2][0] < mid0 and g[2][1] > mid1:
                group.append(g[2])
            if len(group) == 3:
                groups[i] = group
        return groups
    def fit_text(text, width, height, font = cv2.FONT_HERSHEY_SIMPLEX, font_size = 3, color = (0xff, 0xff, 0xff), thick = 5):
        (text_width, text_height) = cv2.getTextSize(text, font, font_size, thick)[0]
        mask = np.zeros((text_height * 3, text_width), dtype = float)
        cv2.putText(mask, text, (0, text_height * 2), font, font_size, 1, thick, cv2.LINE_AA)
        mask = cv2.resize(mask, (min(width, text_width), min(height, text_height * 3)))
        pad_x = (width - mask.shape[1]) // 2
        pad_y = (height - mask.shape[0]) // 2
        mask = cv2.copyMakeBorder(mask, pad_y, height - pad_y, pad_x, width - pad_x, borderType = cv2.BORDER_CONSTANT)
        return cv2.merge(tuple(mask * c for c in color)).astype(np.uint8)

    groups = sort_quads(group_quads(big_quads, small_quads))

    debug_img = orig_img.copy()

    # Visualization
    for q in big_quads:
        cv2.rectangle(debug_img, (q[0], q[1]), (q[2], q[3]), (0xff, 0x00, 0x00), 1)
    num = 0
    for g in groups:
        box = big_quads[g]
        group = groups[g]
        if len(group) != 3:
            continue
        num += 1
        # Visualization
        cv2.rectangle(debug_img, (box[0], box[1]), (box[2], box[3]), (0xff, 0x00, 0xff), 2)
        for q in group:
            cv2.rectangle(debug_img, (q[0], q[1]), (q[2], q[3]), (0x00, 0xff, 0x00), 2)

        centers = [(q[0] + q[2]) * 0.5 + (q[1] + q[3]) * 0.5j for q in group]
        ab_mag = abs(centers[1] - centers[0])
        ac_mag = abs(centers[2] - centers[0])
        bc_mag = abs(centers[2] - centers[1])
        # Move top-left square to index 0
        if ab_mag > bc_mag:
            if ab_mag > ac_mag:
                # C should be the top-left square, swap A and C
                centers[0], centers[2] = centers[2], centers[0]
                group[0], group[2] = group[2], group[0]
            else:
                # B should be the top-left square, swap A and B
                centers[0], centers[1] = centers[1], centers[0]
                group[0], group[1] = group[1], group[0]
        # Make winding order clockwise to ensure that B and C are the top-right and the bottom-left squares respectively
        ab = centers[1] - centers[0]
        ac = centers[2] - centers[0]
        if ab.real * ac.imag - ab.imag * ac.real < 0:
            centers[1], centers[2] = centers[2], centers[1]
            group[1], group[2] = group[2], group[1]

        # Visualization
        for i in range(3):
            cv2.putText(debug_img, ['TL', 'TR', 'BL'][i], (round(centers[i].real) - 16, round(centers[i].imag) + 12), cv2.FONT_HERSHEY_SIMPLEX, 1, (0x00, 0x00, 0xff, 0xff), 2)

        (a, b, c) = centers
        aw = group[0][2] - group[0][0]
        bw = group[1][2] - group[1][0]
        cw = group[2][2] - group[2][0]
        ah = group[0][3] - group[0][1]
        bh = group[1][3] - group[1][1]
        ch = group[2][3] - group[2][1]
        # Helper to normalize a vector and then scale it
        def ellipsize(vec, a, b):
            return (vec.real * a + vec.imag * b * 1j) / abs(vec)
        # Estimate top and left edges
        a_top = ellipsize((a - b) * 1j, aw * 0.5, ah * 0.5)
        b_top = ellipsize((a - b) * 1j, bw * 0.5, bh * 0.5)
        a_left = ellipsize((c - a) * 1j, aw * 0.5, ah * 0.5)
        c_left = ellipsize((c - a) * 1j, cw * 0.5, ch * 0.5)
        # Estimate the perspective
        scale_ab = abs(c_left) / abs(a_left)
        scale_ac = abs(b_top) / abs(a_top)
        # Calculate the D's center
        d = a + (b - a) * scale_ab + (c - a) * scale_ac
        # Estimate right and bottom edges
        b_right = ellipsize((a - c) * 1j, bw * 0.5, bh * 0.5)
        c_bottom = ellipsize((b - a) * 1j, cw * 0.5, ch * 0.5)
        d_right = b_right * scale_ab
        d_bottom = c_bottom * scale_ac
        # Helper to get the intersection point of two rays
        def intersection(ao, ad, bo, bd):
            return ao + ad * (ao.imag * bd.real + bd.imag * bo.real - bo.imag * bd.real - bd.imag * ao.real) / (ad.real * bd.imag - ad.imag * bd.real)
        # Estimate corners
        top_ba = a - b + a_top - b_top
        left_ca = a - c + a_left - c_left
        right_bd = d - b + d_right - b_right
        bottom_cd = d - c + d_bottom - c_bottom
        tl = a + intersection(a_top, top_ba, a_left, left_ca)
        tr = b + intersection(b_top, -top_ba, b_right, -right_bd)
        bl = c + intersection(c_bottom, -bottom_cd, a_left, -left_ca)
        br = d + intersection(d_bottom, bottom_cd, b_right, right_bd)

        # Visualization
        cv2.putText(debug_img, 'BR', (round(d.real) - 16, round(d.imag) + 12), cv2.FONT_HERSHEY_SIMPLEX, 1, (0x00, 0x00, 0xff), 2)
        cv2.line(debug_img, (round(a.real), round(a.imag)), (round(b.real), round(b.imag)), (0x80, 0x80, 0x80), 5)
        cv2.line(debug_img, (round(a.real), round(a.imag)), (round(c.real), round(c.imag)), (0x80, 0x80, 0x80), 5)
        cv2.line(debug_img, (round(b.real), round(b.imag)), (round(d.real), round(d.imag)), (0x80, 0x80, 0x80), 5)
        cv2.line(debug_img, (round(c.real), round(c.imag)), (round(d.real), round(d.imag)), (0x80, 0x80, 0x80), 5)
        #cv2.line(debug_img, (round(a.real), round(a.imag)), (round(a.real + a_top.real), round(a.imag + a_top.imag)), (0x00, 0x80, 0xff), 1)
        #cv2.line(debug_img, (round(b.real), round(b.imag)), (round(b.real + b_top.real), round(b.imag + b_top.imag)), (0x00, 0x80, 0xff), 1)
        #cv2.line(debug_img, (round(a.real), round(a.imag)), (round(a.real + a_left.real), round(a.imag + a_left.imag)), (0xff, 0x80, 0x00), 1)
        #cv2.line(debug_img, (round(c.real), round(c.imag)), (round(c.real + c_left.real), round(c.imag + c_left.imag)), (0xff, 0x80, 0x00), 1)
        #cv2.line(debug_img, (round(b.real), round(b.imag)), (round(b.real + b_right.real), round(b.imag + b_right.imag)), (0x80, 0xff, 0x00), 1)
        #cv2.line(debug_img, (round(d.real), round(d.imag)), (round(d.real + d_right.real), round(d.imag + d_right.imag)), (0x80, 0xff, 0x00), 1)
        #cv2.line(debug_img, (round(c.real), round(c.imag)), (round(c.real + c_bottom.real), round(c.imag + c_bottom.imag)), (0x00, 0xff, 0x80), 1)
        #cv2.line(debug_img, (round(d.real), round(d.imag)), (round(d.real + d_bottom.real), round(d.imag + d_bottom.imag)), (0x00, 0xff, 0x80), 1)
        cv2.line(debug_img, (round(tl.real), round(tl.imag)), (round(tr.real), round(tr.imag)), (0x00, 0x80, 0x00), 2)
        cv2.line(debug_img, (round(tl.real), round(tl.imag)), (round(bl.real), round(bl.imag)), (0x00, 0x80, 0x00), 2)
        cv2.line(debug_img, (round(tr.real), round(tr.imag)), (round(br.real), round(br.imag)), (0x00, 0x80, 0x00), 2)
        cv2.line(debug_img, (round(bl.real), round(bl.imag)), (round(br.real), round(br.imag)), (0x00, 0x80, 0x00), 2)

        # Calculate transformation matrix
        resolution = max(box[2] - box[0], box[3] - box[1])
        src_pts = np.float32([[x.real, x.imag] for x in [tl, tr, bl, br]])
        dst_pts = np.float32([[0, 0], [resolution, 0], [0, resolution], [resolution, resolution]])
        tfm_mat = cv2.getPerspectiveTransform(src_pts, dst_pts)
        inv_mat = cv2.getPerspectiveTransform(dst_pts, src_pts)
        # Undistort and read the QR code
        qr_img = cv2.warpPerspective(orig_img, tfm_mat, [resolution, resolution])
        if len(read_qr(qr_img)) > 0:
            qr_data = read_qr(qr_img)[0].data.decode()
            if not num in text:
                text[num] = []
            text[num].append(qr_data)
            # Draw the text, apply inverse transformation to it and overlay on top of the original image
            text_img = cv2.warpPerspective(fit_text(qr_data, resolution, resolution), inv_mat, orig_img.shape[1::-1])
            orig_img = cv2.multiply(1 - text_img.astype(float) / 255.0, orig_img.astype(float)).astype(np.uint8)
            orig_img = cv2.add((text_img.astype(float) * (0.0, 0.0, 1.0)).astype(np.uint8), orig_img)

        #cv2.imshow('QR #%d' % g, qr_img)
        cv2.imwrite('qr'+str(num)+'.jpg', qr_img)


    #cv2.imshow('Debug', debug_img)
    cv2.imwrite('debug_img.jpg', debug_img)
    #cv2.imshow('Overlay', orig_img)
    cv2.imwrite('orig_img.jpg', orig_img)
    return len(groups), text
    """
    while not cv2.waitKey(1000) & 0xff in [ord(c) for c in 'Qq'] + [0x1b]:
        pass

    cv2.destroyAllWindows()
    """