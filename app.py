import sys
from PIL import Image
import xml.etree.ElementTree as ET
import os
import matplotlib.pyplot as plt
import json


def parse_annotations(img_id, xml_path, max_category_id, max_annotation_id, categories):
    """ Function that builds the annotations list of a speciefic image

        Parameters
        ----------
        img_id: int
            Id of the image

        xml_path: str
            Path to the xml file with annotations info

        max_category_id: int
            Max category id until now. Increment in case of new found category

        max_annotation_id: int
            Max annotation id until now. Increment at every bounding box

        Returns
        -------
        bbox_coordinates: list
            list of annotations for this image

    """
    # parse xml file
    tree = ET.parse(xml_path)
    root = tree.getroot() # get root object

    bbox_coordinates = []
    for object in root.findall('object'):
        category = object[0].text

        # bbox coordinates
        xmin = int(object[4][0].text)
        ymin = int(object[4][1].text)
        xmax = int(object[4][2].text)
        ymax = int(object[4][3].text)

        if category in categories: # category already found
            cat_id = categories[category]['id']
        else:   # new category
            max_category_id += 1
            categories[category] = {'id':max_category_id, 'name':category, 'supercategory': None}

        max_annotation_id += 1  # increment annotation_id
        bbox_coordinates.append({'id': max_annotation_id,
                                'image_id': img_id,
                                'category_id': categories[category]['id'],
                                'bbox': [xmin, ymin, xmax-xmin, ymax-ymin]})    # [x, y, width, height]

    return bbox_coordinates


if __name__ == "__main__":
    imagedir = sys.argv[1]
    xmldir = sys.argv[2]
    outputdir = sys.argv[3]

    max_width = 800
    max_height = 450

    categories = {}
    category_id = 0
    annotation_id = 0

    COCO_dic = {'categories': [],
                'images':[],
                'annotations':[]
                }

    # names of all the images
    filenames = [os.path.splitext(name)[0] for name in os.listdir(imagedir) if os.path.splitext(name)[-1]=='.jpg']

    # for every filename (img)
    for i, filename in enumerate(filenames):
        print(filename)
        # read image
        img = Image.open(os.path.join(imagedir, filename+'.jpg'))
        # get annotation and relative bounding boxes
        xml_path = os.path.join(xmldir, filename+'.xml')
        bboxes = parse_annotations(filename, xml_path, category_id, annotation_id, categories)

        # resize width if necessary
        if img.size[0] > max_width:
            scale_width = max_width/img.size[0] # scale_widht is needed to adjust the bbox
            img = img.resize((max_width, img.size[1]))
            # resize the bounding boxes
            for bb in bboxes:
                bb['bbox'][0] = round(bb['bbox'][0] * scale_width, 2) #scale x
                bb['bbox'][2] = round(bb['bbox'][2] * scale_width, 2) #scale width

        # resize height if necessary
        if img.size[1] > max_height:
            scale_height = max_height/img.size[1]   # scale_height is needed to adjust the bbox
            img = img.resize((img.size[0], max_height))
            for bb in bboxes:
                bb['bbox'][1] = round(bb['bbox'][1] * scale_height, 2) #scale y
                bb['bbox'][3] = round(bb['bbox'][3] * scale_height, 2) #scale height


        # append annotations
        COCO_dic['annotations'] += bboxes
        # append image information
        COCO_dic['images'].append({'id':filename, 'width': img.size[0], 'height': img.size[1], 'filename':os.path.join(imagedir, filename+'.jpg')})

        #save image
        print(img.size)
        img.save(os.path.join(outputdir,'images', filename+'.jpg'))

    COCO_dic['categories'] = list(categories.values())

    # save json
    with open(os.path.join(outputdir, 'COCO_output.json'), 'w') as fp:
        json.dump(COCO_dic, fp, indent=4)
