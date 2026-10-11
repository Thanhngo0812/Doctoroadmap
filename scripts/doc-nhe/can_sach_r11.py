"""Book-and-class balanced ERM, not group-DRO, for fixed A1 experiments."""
import numpy as np
import hoc_tieu_de as base


def training_arrays(data,heldout=()):
    x,y,names=base.training_arrays(data,heldout)
    weights=[]
    for name in names:
        labels=data[name]['y']
        labels=labels[labels>=0]
        values,counts=np.unique(labels,return_counts=True)
        if not len(values):
            raise ValueError('Cannot balance a book without labelled training rows')
        part=np.zeros(len(labels),dtype=float)
        for value,count in zip(values,counts,strict=True):
            part[labels==value]=len(y)/(len(names)*len(values)*count)
        weights.extend(part)
    weights=np.asarray(weights)
    return x,y,weights,names
