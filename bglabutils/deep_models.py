import torch
from torch.masked import masked_tensor, as_masked_tensor
from torch.utils.data import Dataset, DataLoader
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from tqdm.notebook import tqdm
import plotly.graph_objects as go
import matplotlib.pylab as plt

class CustomDataset(Dataset):
    def __init__(self, dataframe, features_in, conditions_in, mask_in, window_size=24*2, step=1, device='cpu'):
        self.dataframe = dataframe.copy()
        self.window_size = window_size
        self.features = features_in
        self.conditions = conditions_in
        self.mask = mask_in
        self.step = step
        self.data = torch.tensor(self.dataframe[self.features].to_numpy(dtype=np.float32)).to(device)
        self.conditions = torch.tensor(self.dataframe[self.conditions].to_numpy(dtype=np.float32)).to(device)
        self.masks = torch.tensor(self.dataframe[self.mask].to_numpy(dtype=np.bool_)).to(device)


    def __getitem__(self, index):
        ind = index * self.step
        window = self.data[ind: ind + self.window_size]
        conditions = self.conditions[ind: ind + self.window_size]
        mask_out = self.masks[ind: ind + self.window_size]

        return window.squeeze(), conditions.squeeze(), mask_out.squeeze()

    def __len__(self):
        return int((len(self.dataframe)))
class Encoder(nn.Module):
    def __init__(self, n_input, nz,  device):
        super(Encoder, self).__init__()

        # Device
        self.device = device

        # Encoder: (nc, isize, isize) -> (nef*8, isize//16, isize//16)
        self.encoder = nn.Sequential(
            nn.Linear(n_input, nz*16),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(num_features=nz*16),

            nn.Linear(nz*16, nz*8),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*8),

            nn.Linear(nz*8, nz*4),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*4),

            nn.Linear(nz*4, nz*2),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*2)
        )

        # Map the encoded feature map to the latent vector of mean, (log)variance
        # out_size = isize // 16
        self.mean = nn.Linear(nz*2, nz)
        self.logvar = nn.Linear(nz*2, nz)

    @staticmethod
    def reparametrize(mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def forward(self, inputs, conditions):
        # Batch size
        inputs = torch.cat([inputs, conditions], dim=-1)
        # print(inputs.shape, conditions.shape)

        batch_size = inputs.size(0)
        # Encoded feature map
        hidden = self.encoder(inputs)
        # Reshape
        # hidden = hidden.view(batch_size, -1)
        # Calculate mean and (log)variance

        mean, logvar = self.mean(hidden), self.logvar(hidden)
        # Sample
        latent_z = self.reparametrize(mean, logvar)

        return latent_z, mean, logvar


class Decoder(nn.Module):
    def __init__(self, ndf, nz, n_cond, device):
        super(Decoder, self).__init__()

        # Map the latent vector to the feature map space
        self.ndf = ndf
        self.device = device
        # self.out_size = isize // 16
        # print("nz ", nz+n_cond)
        self.decoder_dense = nn.Sequential(
            nn.Linear(nz+n_cond, nz*2),
            nn.ReLU(True),

            nn.Linear(nz*2, nz*4),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*4),

            nn.Linear(nz*4, nz*8),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*8),

            nn.Linear(nz*8, nz*16),
            nn.LeakyReLU(0.2, True),
            nn.BatchNorm1d(nz*16),

            nn.Linear(nz*16, ndf-n_cond)
        )


    def forward(self, input, conditions):
        input_cat = torch.cat([input, conditions], dim=-1)
        # batch_size = input.size(0)
        # print(input_cat.size)
        output = self.decoder_dense(input_cat)#.view(
        #    batch_size, self.ndf*8, self.out_size, self.out_size)
        # print(hidden.size)
        # output = self.decoder_conv(hidden)
        return output



class VAE(nn.Module):
    def __init__(self, ndf=32, nz=100, n_cond=1, device=torch.device("cuda:0"), is_train=True):
        super(VAE, self).__init__()

        self.nz = nz
        # self.isize=isize
        # Encoder
        self.encoder = Encoder(n_input=ndf, nz=nz, device=device)
        # Decoder
        self.decoder = Decoder(ndf=ndf, nz=nz, n_cond = n_cond, device=device)
        self.mdevice = device

        if is_train == False:
            for param in self.encoder.parameters():
                param.requires_grad = False
            for param in self.decoder.parameters():
                param.requires_grad = False

    def forward(self, x, conditions):
        latent_z, mean, logvar = self.encoder(x, conditions)
        # print("latern ", latent_z.shape)
        rec_x = self.decoder(latent_z, conditions)
        return rec_x, mean, logvar, conditions

    def encode(self, x, conditions):
        latent_z, _, _ = self.encoder(torch.cat([x, conditions], dim=1))
        return latent_z

    def decode(self, z, conditions):
        return self.decoder(torch.cat([z, conditions], dim=1))

    @staticmethod
    def reparametrize(mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return mu + eps*std

    def sample(self, size):
        sample = torch.randn(size, self.nz).to(self.device)
        return self.decode(sample)

    @property
    def device(self): return next(self.parameters()).device

    def loss_function(self, recon_x, x, mu, logvar, mask):
        batch_size = recon_x.shape[0]
        MSE = F.mse_loss(torch.masked_select(recon_x.view(batch_size, -1), mask.view(batch_size, -1)),
                         torch.masked_select(x.view(batch_size, -1), mask.view(batch_size, -1)), reduction='sum')
        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return MSE, KLD


    def train_vae(self, data, features, conditions, masks, epochs=300, optimizer = None, figure=None):

        def single_epoch_train(lpbar, dataloader):
            self.train()
            train_mse, train_kld, train_loss = 0, 0, 0
            for ldata, condition, mask in dataloader:
                ldata = ldata.to(self.mdevice)
                condition = condition.to(self.mdevice)
                mask = mask.to(self.mdevice)
                optimizer.zero_grad()
                recon_batch, mu, logvar, cond_out = self.__call__(ldata, condition)
                mse_loss, kld_loss = self.loss_function(recon_batch, ldata, mu, logvar, mask)
                loss = mse_loss + kld_loss
                loss.backward()
                train_loss += loss.item();
                train_mse += mse_loss.item();
                train_kld += kld_loss.item()
                optimizer.step()
                amount = np.ones_like(mask.detach().to('cpu'))[mask.detach().to('cpu')].sum()
                lpbar.set_description(f"[KL: {kld_loss.item() / len(data) :.2f}] [MSE: {mse_loss.item() / amount: .2f}]")
                lpbar.update(1)
            # print(kld_loss.item() / len(data), mse_loss.item() / len(data))
            return kld_loss.item() / len(data), mse_loss.item() / amount

        if not optimizer:
            optimizer = torch.optim.Adam(self.parameters(), lr=1e-5)

        tdata = CustomDataset(data, features, conditions, masks, window_size=1)
        l_dataloader = DataLoader(tdata, batch_size=2048)

        my_metrics = [[], []]
        # fig = go.Figure(layout_xaxis_range=[0, epochs])
        # f = go.FigureWidget(fig)
        # f.add_scatter(y=my_metrics[1])
        # f
        with tqdm(total=epochs * len(l_dataloader), desc=f"[KL: ?] [MSE: ?]") as pbar:
            for epoch in range(1, epochs + 1):
                # print(epoch)
                train_results = single_epoch_train(pbar, l_dataloader)
                my_metrics[0].append(train_results[0])
                my_metrics[1].append(train_results[1])
                if figure:
                    figure.data[0].y = my_metrics[1]
            plt.plot(my_metrics[0], label='kld')
            plt.plot(my_metrics[1], label='mse')
            plt.legend()
            plt.show()





class Encoder2(nn.Module):
    def __init__(self, in_config, ncond, device):
        super(Encoder2, self).__init__()

        # Device
        self.device = device

        self.config = in_config

        def gen_block(in_shap, out_shape):
            return [nn.Linear(in_shap, out_shape),
                    nn.LeakyReLU(0.2, True), ]
            # nn.BatchNorm1d(num_features=out_shape)]

        layers = [(gen_block(in_config[0]['in'] + ncond, in_config[0]['out']))]
        layers += [gen_block(i['in'], i['out']) for i in in_config[1:-1]]
        layers = [x for xs in layers for x in xs]
        self.encoder = nn.Sequential(*layers)

        # Map the encoded feature map to the latent vector of mean, (log)variance
        # out_size = isize // 16
        self.mean = nn.Linear(in_config[-1]['in'], in_config[-1]['out'])
        self.logvar = nn.Linear(in_config[-1]['in'], in_config[-1]['out'])

    @staticmethod
    def reparametrize(mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, inputs, conditions):
        # Batch size
        inputs = torch.cat([inputs, conditions], dim=-1)
        # print(inputs.shape, conditions.shape)

        batch_size = inputs.size(0)
        # print(inputs.device, self.encoder.device)
        # Encoded feature map
        hidden = self.encoder(inputs)
        # Reshape
        # hidden = hidden.view(batch_size, -1)
        # Calculate mean and (log)variance

        mean, logvar = self.mean(hidden), self.logvar(hidden)
        # Sample
        latent_z = self.reparametrize(mean, logvar)

        return latent_z, mean, logvar


class Decoder2(nn.Module):
    def __init__(self, in_config, ncond, device='cpu'):
        super(Decoder2, self).__init__()

        # Device
        self.device = device

        def gen_block(in_shape, out_shape):
            return [nn.Linear(in_shape, out_shape),
                    nn.LeakyReLU(0.2, True), ]
            # nn.BatchNorm1d(num_features=out_shape)]

        layers = [(nn.Linear(in_config[-1]['out'] + ncond, in_config[-1]['in']),
                   nn.ReLU(True))]
        layers += [gen_block(i['out'], i['in']) for i in in_config[::-1][1:-1]]
        layers = [x for xs in layers for x in xs]
        layers.append(nn.Linear(in_config[1]['in'], in_config[0]['in']))

        self.decoder_dense = nn.Sequential(*layers)

    def forward(self, input, conditions):
        input_cat = torch.cat([input, conditions], dim=-1)
        # batch_size = input.size(0)
        # print(input_cat.size)
        output = self.decoder_dense(input_cat)  # .view(
        #    batch_size, self.ndf*8, self.out_size, self.out_size)
        # print(hidden.size)
        # output = self.decoder_conv(hidden)
        return output


class VAE2(nn.Module):
    def __init__(self, in_config, ncond=1, device=torch.device("cuda:0"), is_train=True):
        super(VAE2, self).__init__()
        # print(device)
        self.config = in_config
        # Encoder
        self.encoder = Encoder2(self.config, ncond, device=device)
        # Decoder
        self.decoder = Decoder2(self.config, ncond, device=device)
        self.device = device

        if is_train == False:
            for param in self.encoder.parameters():
                param.requires_grad = False
            for param in self.decoder.parameters():
                param.requires_grad = False

    def forward(self, x, conditions):
        latent_z, mean, logvar = self.encoder(x, conditions)
        # print("latern ", latent_z.shape)
        rec_x = self.decoder(latent_z, conditions)
        return rec_x, mean, logvar, conditions

    def encode(self, x, conditions):
        latent_z, _, _ = self.encoder(torch.cat([x, conditions], dim=1))
        return latent_z

    def decode(self, z, conditions):
        return self.decoder(torch.cat([z, conditions], dim=1))

    @staticmethod
    def reparametrize(mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def sample(self, size):
        sample = torch.randn(size, self.nz).to(self.device)
        return self.decode(sample)

    @property
    def device(self):
        return next(self.parameters()).device


    def loss_function(self, recon_x, x, mu, logvar, mask):
        batch_size = recon_x.shape[0]
        MSE = F.mse_loss(torch.masked_select(recon_x.view(batch_size, -1), mask.view(batch_size, -1)),
                         torch.masked_select(x.view(batch_size, -1), mask.view(batch_size, -1)), reduction='sum')
        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return MSE, KLD


    def train_vae(self, data, features, conditions, masks, epochs=300, optimizer = None):

        def single_epoch_train(pbar, ):
            self.train()
            train_mse, train_kld, train_loss = 0, 0, 0
            for data, condition, mask in dataloader:
                data = data.to(self.device)
                condition = condition.to(self.evice)
                optimizer.zero_grad()
                recon_batch, mu, logvar, cond_out = self.__call__(data, condition)
                mse_loss, kld_loss = self.loss_function(recon_batch, data, mu, logvar, mask)
                loss = mse_loss + kld_loss
                loss.backward()
                train_loss += loss.item();
                train_mse += mse_loss.item();
                train_kld += kld_loss.item()
                optimizer.step()
                pbar.set_description(f"[KL: {kld_loss.item() / len(data) :.2f}] [MSE: {mse_loss.item() / len(data): .2f}]")
                pbar.update(1)
            print(kld_loss.item() / len(data), mse_loss.item() / len(data))
            return kld_loss.item() / len(data), mse_loss.item() / len(data)

        if not optimizer:
            optimizer = torch.optim.Adam(self.parameters(), lr=1e-5)

        tdata = CustomDataset(data, features, conditions, masks, window_size=1)
        dataloader = DataLoader(tdata, batch_size=2048)

        f = go.FigureWidget()
        my_metrics = [[], []]

        f.add_scatter(y=my_metrics[0])
        f.add_scatter(y=my_metrics[1])
        f
        with tqdm(total=epochs * len(dataloader), desc=f"[KL: ?] [MSE: ?]") as pbar:
            for epoch in range(1, epochs + 1):
                print(epoch)
                train_results =  single_epoch_train.train_vae(pbar, dataloader)
                my_metrics[0].append(train_results[0])
                my_metrics[1].append(train_results[1])
                f.data[0].y = my_metrics[0]
                f.data[1].y = my_metrics[1]


