import torch
import torch.nn as nn
import torch.nn.functional as F
from models.loss.Dist import Dist
import pandas as pd
import numpy as np
from utils.dist import dist_func
# from scipy import stats


# class OneRestLoss_arpl(nn.Module):
class OrdlLoss(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.Dist = Dist(num_classes=len(config.dataset.known_class)+1, num_centers=config.num_centers, feat_dim=config.backbone.feat_dim)
        # self.points = self.Dist.centers#归一化中心
        self.a = config.alpha
        self.b = config.beta
        # self.radius1 = nn.Parameter(torch.tensor([1.0]))
        # self.radius2 = nn.Parameter(torch.tensor([0.0])) # 径r是待优化参数
        self.k_margin_loss = nn.MarginRankingLoss(margin=1)
        self.u_margin_loss = nn.MarginRankingLoss(margin=1)

        self.losses = {}

    def forward(self, feat, centers, radius1, radius2, labels=None):
        num_classes = len(self.config.dataset.known_class)
        loss = torch.tensor(0.0,dtype=torch.float32).cuda()
        dist_dot_p = dist_func(feat, center=centers, num_classes=num_classes+1, num_centers=1, metric='dot')
        dist_l2_p = dist_func(feat, center=centers, num_classes=num_classes+1, num_centers=1, metric='l2')

        logits = dist_dot_p - dist_l2_p
        if labels is not None:
            b_dot = []
            for i in range(logits.size(1) - 1):
                temp = torch.vstack((logits[:, -1], logits[:, i]))
                b_dot.append(temp.t())

            cla_loss = 0.0
            ge_loss = 0.0
            
            one_hot_labels = pd.get_dummies(labels.cpu().numpy())
            # num_class = len(one_hot_labels.columns)
            for class_label in one_hot_labels.columns:
                one_hot = (torch.from_numpy(np.array(one_hot_labels[class_label]))).long().cuda()
                cla_loss += F.cross_entropy(b_dot[class_label], one_hot)

                k_k_dist = dist_l2_p[:, class_label][one_hot.bool()] #当前闭集类到当前对应闭集中心的距离
                u_k_dist = dist_l2_p[:, class_label][(1 - one_hot).bool()]#当前开集类到当前对应闭集中心的距离
                u_u_dist = dist_l2_p[:, -1][(1 - one_hot).bool()]#当前开集类到开集中心的距离
                # k_u_dist = dist_l2_p[:, -1][one_hot.bool()]#当前闭集类到开集中心的距离
                k_k_target = torch.ones(k_k_dist.size(0)).cuda()
                u_u_target = torch.ones(u_u_dist.size(0)).cuda()
                
                open_risk = self.u_margin_loss(radius1,u_u_dist,u_u_target)
                k_margin_loss = self.k_margin_loss(radius2, k_k_dist, k_k_target) + self.k_margin_loss(radius2,
                                                                                                            u_k_dist,
                                                                                                            -u_u_target)  

                ge_loss += ((1-self.a)*open_risk + self.a*k_margin_loss)
            loss = (1-self.b)*cla_loss + self.b*ge_loss
            self.losses["cla"] = cla_loss
            self.losses["ge"] = ge_loss
            return logits, loss
        else:
            return logits
            

        # return logits, loss