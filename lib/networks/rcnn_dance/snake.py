import torch.nn as nn
import torch


class CircConv(nn.Module):
    def __init__(self, state_dim, out_state_dim=None, n_adj=4):
        super(CircConv, self).__init__()

        self.n_adj = n_adj
        out_state_dim = state_dim if out_state_dim is None else out_state_dim
        self.fc = nn.Conv1d(state_dim,
                            out_state_dim,
                            kernel_size=self.n_adj * 2 + 1)

    def forward(self, input, adj):
        input = torch.cat(
            [input[..., -self.n_adj:], input, input[..., :self.n_adj]], dim=2)
        return self.fc(input)


class DilatedCircularConv(nn.Module):
    def __init__(self, state_dim, out_state_dim=None, n_adj=4, dilation=1):
        super(DilatedCircularConv, self).__init__()

        self.n_adj = n_adj
        self.dilation = dilation
        out_state_dim = state_dim if out_state_dim is None else out_state_dim
        self.fc = nn.Conv1d(state_dim,
                            out_state_dim,
                            kernel_size=self.n_adj * 2 + 1,
                            dilation=self.dilation)

    def forward(self, input):
        if self.n_adj != 0:
            input = torch.cat([
                input[..., -self.n_adj * self.dilation:], input,
                input[..., :self.n_adj * self.dilation]
            ],
                              dim=2)
        return self.fc(input)


class SnakeBlock(nn.Module):
    def __init__(self, state_dim, out_state_dim, n_adj=4, dilation=1):
        super(SnakeBlock, self).__init__()

        self.conv = DilatedCircularConv(state_dim, out_state_dim, n_adj,
                                        dilation)
        self.relu = nn.ReLU(inplace=True)
        self.norm = nn.BatchNorm1d(out_state_dim)

    def forward(self, x):
        x = self.conv(x)
        x = self.relu(x)
        x = self.norm(x)

        return x


# _conv_factory = {'grid': CircConv, 'dgrid': DilatedCircConv}

# class BasicBlock(nn.Module):
#     def __init__(self,
#                  state_dim,
#                  out_state_dim,
#                  conv_type,
#                  n_adj=4,
#                  dilation=1):
#         super(BasicBlock, self).__init__()

#         self.conv = _conv_factory[conv_type](state_dim, out_state_dim, n_adj,
#                                              dilation)
#         self.relu = nn.ReLU(inplace=True)
#         self.norm = nn.BatchNorm1d(out_state_dim)

#     def forward(self, x, adj=None):
#         x = self.conv(x, adj)
#         x = self.relu(x)
#         x = self.norm(x)
#         return x

# class Snake(nn.Module):
#     def __init__(self, state_dim, feature_dim, conv_type='dgrid'):
#         super(Snake, self).__init__()

#         self.head = BasicBlock(feature_dim, state_dim, conv_type)

#         self.res_layer_num = 7
#         dilation = [1, 1, 1, 2, 2, 4, 4]
#         for i in range(self.res_layer_num):
#             conv = BasicBlock(state_dim,
#                               state_dim,
#                               conv_type,
#                               n_adj=4,
#                               dilation=dilation[i])
#             self.__setattr__('res' + str(i), conv)

#         fusion_state_dim = 256
#         self.fusion = nn.Conv1d(state_dim * (self.res_layer_num + 1),
#                                 fusion_state_dim, 1)
#         self.prediction = nn.Sequential(
#             nn.Conv1d(state_dim * (self.res_layer_num + 1) + fusion_state_dim,
#                       256, 1), nn.ReLU(inplace=True), nn.Conv1d(256, 64, 1),
#             nn.ReLU(inplace=True), nn.Conv1d(64, 2, 1))

#     def forward(self, x, adj):
#         states = []

#         x = self.head(x, adj)
#         states.append(x)
#         for i in range(self.res_layer_num):
#             x = self.__getattr__('res' + str(i))(x, adj) + x
#             states.append(x)

#         state = torch.cat(states, dim=1)
#         global_state = torch.max(self.fusion(state), dim=2, keepdim=True)[0]
#         global_state = global_state.expand(global_state.size(0),
#                                            global_state.size(1), state.size(2))
#         state = torch.cat([global_state, state], dim=1)
#         x = self.prediction(state)

#         return x


class SnakeNet(nn.Module):
    def __init__(self, state_dim, edge_feature_dim):
        super(SnakeNet, self).__init__()

        self.head = SnakeBlock(edge_feature_dim, state_dim)

        self.res_layer_num = 7  # TODO: decrease
        dilation = [1, 1, 1, 2, 2, 4, 4]
        for i in range(self.res_layer_num):
            conv = SnakeBlock(state_dim,
                              state_dim,
                              n_adj=4,
                              dilation=dilation[i])
            self.__setattr__('res' + str(i), conv)

        fusion_state_dim = 256

        self.fusion = nn.Conv1d(state_dim * (self.res_layer_num + 1),
                                fusion_state_dim, 1)
        self.prediction = nn.Sequential(
            nn.Conv1d(state_dim * (self.res_layer_num + 1) + fusion_state_dim,
                      256, 1), nn.ReLU(inplace=True), nn.Conv1d(256, 64, 1),
            nn.ReLU(inplace=True), nn.Conv1d(64, 2, 1))

    def forward(self, x):
        states = []

        x = self.head(x)
        states.append(x)
        for i in range(self.res_layer_num):
            x = self.__getattr__('res' + str(i))(x) + x
            states.append(x)

        state = torch.cat(states, dim=1)

        back_out = self.fusion(state)
        global_state = torch.max(back_out, dim=2, keepdim=True)[0]

        global_state = global_state.expand(global_state.size(0),
                                           global_state.size(1), state.size(2))
        state = torch.cat([global_state, state], dim=1)
        x = self.prediction(state)

        return x
