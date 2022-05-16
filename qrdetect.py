from predict import predict
from helpers import draw_bboxs, resizer
import numpy as np

def get_quads(image, weights = "best.pt"):
    image_path = image
    
    pred_list, pred = predict(
    weights=weights,
    source=image_path,
    imgsz=[608, 608])

    pred = pred[0].numpy()[:, :].tolist()
    
    big_quads = []
    small_quads = []
    
    for i in range(len(np.array(pred))):
        if pred[i][-1] == 0:
            small_quads.append(pred[i])
        elif pred[i][-1] == 1:
            big_quads.append(pred[i])
    if len(big_quads) < 1 or len(small_quads) < 1:
        return [], []
    big_quads = np.hstack((np.array(big_quads)[:, :4], np.array(big_quads)[:, -1].reshape(-1, 1))).tolist()
    small_quads = np.hstack((np.array(small_quads)[:, :4], np.array(small_quads)[:, -1].reshape(-1, 1))).tolist()
    for quad in big_quads:
        quad.pop()
        for i in range(len(quad)):
            quad[i] = int(quad[i])
    for quad in small_quads:
        quad.pop()
        for i in range(len(quad)):
            quad[i] = int(quad[i])
    return big_quads, small_quads