import tqdm
import random
import os
import numpy as np
import torch
import math
from resources.utils import *


DEFAULT_MAP = """A1 => nha_lau
A2 => nha_may_ngoi
A3 => nha_rong
A4 => nha_san
A5 => nha_biet_thu
A6 => nha_tren_cay
A7 => nha_go
A8 => nha_chung_cu
A9 => nha_tret
A10 => nha_ky_tuc_xa
A11 => tivi
A12 => den
A13 => dong_ho
A14 => cau_thang
A15 => chia_khoa
A16 => o_khoa
A17 => ban_ghe_sofa
A18 => ban_tho
A19 => dien_thoai_ban
A20 => tranh_anh_treo_tuong
A21 => ke_sach
A22 => cai_chao
A23 => cai_am
A24 => con_dao
A25 => may_say_sinh_to
A26 => TU_LANH
A27 => NOI
A28 => BEP_GA
A29 => MUONG
A30 => DOI_DUA
A31 => BAT
A32 => GIUONG
A33 => QUAT
A34 => MAY_TINH
A35 => BAN_LA
A36 => REM
A37 => thuoc_ke
A38 => cai_keo
A39 => com_pa
A40 => cuc_tay
A41 => ho_dan
A42 => but_chi
A43 => but_bi
A44 => bang_phan
A45 => vien_phan
A46 => got_but_chi
A47 => sua_chua
A48 => ca_phe
A49 => nuoc_uong
A50 => banh_mi
A51 => bun
A52 => mi_quang
A53 => xoi
A54 => pho
A55 => chao
A56 => trung_op_la
A57 => nang
A58 => mat troi
A59 => may
A60 => gio
A61 => nong
A62 => mat
A63 => lanh
A64 => nhiet_do
A65 => tuyet
A66 => suong_mu
A67 => tho_xay
A68 => tho_lam_mong
A69 => cat_toc
A70 => sua_xe
A71 => tho_son
A72 => duong_bo
A73 => duong_sat
A74 => duong_thuy
A75 => duong_hang_khong
A76 => cap_treo
A77 => may_bay
A78 => cano_cao_toc
A79 => xe_may
A80 => xe_dap
A81 => xe_buyt
A82 => thuyen_buom
A83 => xe_canh_sat
A84 => xe_moto
A85 => tau_hoa
A86 => xe_tai
A87 => xe_hoi
A88 => xich_lo
A89 => khinh_khi_cau
A90 => xe_cuu_hoa
A91 => tau_dien_ngam
A92 => con_cho
A93 => con_meo
A94 => con_ca
A95 => con_chuot
A96 => con_rua
A97 => con_chim
A98 => con_bo
A99 => con_ga
A100 => con_ngua
A101 => con_heo
A102 => con_lua
A103 => con_de
A104 => con_trau
A105 => con_ong
A106 => con_tom
A107 => boi
A108 => cau_truot
A109 => chay
A110 => tha_dieu
A111 => nhay_day
A112 => da_cau
A113 => da_bong
A114 => cau_ca
A115 => cam_trai
A116 => keo_co
A117 => con_lua
A118 => may_anh
A119 => mu_luoi_trai
A120 => ong_nhom"""





def filter_outliers(data):
    # Calculate the quartiles
    q1 = np.percentile(data, 20, axis=(1, 2))
    q3 = np.percentile(data, 70, axis=(1, 2))
    
    # Calculate the interquartile range (IQR)
    iqr = q3 - q1
    
    # Calculate the lower and upper bounds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Filter out the outliers, replace with the median
    filtered_data = np.where((data >= lower_bound[:, None, None]) & (data <= upper_bound[:, None, None]), data, np.median(data, axis=(1, 2), keepdims=True))

    return filtered_data


class DSL:
    def __init__(self,
                 dataset_path,
                 n_frames=320,
                 batch_size=1,
                 map_file=None,
                 random_seed=42,
                 cache_folder=None
                 ) -> None:
        '''
        Depth Sign Language Dataset Loader (Preprocessing and Data Augmentation)
        '''
        self.dataset_path = dataset_path
        self.n_frames = n_frames
        self.batch_size = batch_size
        self.random_seed = random_seed
        self.cache_folder = cache_folder
        if map_file is not None:
            # Load the map file
            with open(map_file, 'r') as f:
                self.map_txt = f.read()
        else:
            self.map_txt = DEFAULT_MAP
        self.map = {x.split(' => ')[0]: x.split(' => ')[1].replace('\n', '') for x in self.map_txt.split('\n') if '=>' in x}
        self.classes = []
        self.persons = []

        self.dataset = {}
        self.get_dataset_info()

    def get_dataset_info(self):
    
        # Get the dataset path
        data_batch = os.listdir(self.dataset_path)
        print(f"Gathering dataset information from {len(data_batch)} batches...\n")
        for i, batch in tqdm.tqdm(enumerate(data_batch)):
            # Get the batch path
            batch_path = os.path.join(self.dataset_path, batch)
            
            class_ = batch.split('P')[0]
            print(batch_path)
            person_ = batch.split('P')[1]

            mapped_class = self.map[class_]
            if mapped_class not in self.classes:
                self.classes.append(mapped_class)
            
            if person_ not in self.persons:
                self.persons.append(person_)
            if mapped_class not in self.dataset:
                self.dataset[mapped_class] = {}
            if person_ not in self.dataset[mapped_class]:
                self.dataset[mapped_class][person_] = {'rgb':[],'pose': []}

            for data_point in os.listdir(os.path.join(batch_path, 'rgb')):
                avi_file = os.path.join(batch_path,'rgb', data_point)
                pose_name = data_point.replace('.avi','.npy')
                pose_file = os.path.join(batch_path,'mediapipe_landmarks',pose_name)
                
            
                if  os.path.exists(pose_file) and pose_file :
                    
                    self.dataset[mapped_class][person_]['rgb'].append(avi_file)
                    self.dataset[mapped_class][person_]['pose'].append(pose_file)
                
     
        print(f"Loaded {len(self.classes)} classes {self.classes}")
        print(f"Loaded {len(self.persons)} persons {self.persons}")

    def divide_filter(self,filter_list,ratios:list,randomize=True):
        '''
        Divide filtered list into ratios, e.g. [0.7,0.2,0.1]
        '''
        if sum(ratios) != 1:
            raise ValueError("Sum of ratios must be 1.")
        if not isinstance(ratios,list):
            raise ValueError("Ratios must be a list.")
        if len(ratios) < 2:
            raise ValueError("Ratios must be greater than 1.")
        
        #shuffle the dataset
        zipped = list(zip(filter_list['rgb'],filter_list['pose'],filter_list['class']))
        if randomize:
            random.seed(self.random_seed)
            random.shuffle(zipped)
        filtered_list = {'rgb':[],'pose':[],'class':[],'len':0}
        result_list = []
        for i in range(len(ratios)):
            result_list.append(filtered_list.copy())

        return result_list


    def filter(self,classes:list=None,persons:list=None,randomize=True):
        filtered_list = {'rgb':[],'pose': [],'class':[],'len':0}
        #if no classes are specified, use all classes
        if classes is None:
            classes = self.classes
        #if no persons are specified, use all persons
        if persons is None:
            persons = self.persons
        for class_ in classes:
            for person in persons:
                if person not in self.dataset[class_]:
                    continue
              
                filtered_list['rgb'].extend(self.dataset[class_][person]['rgb'])
                filtered_list['pose'].extend(self.dataset[class_][person]['pose'])
                filtered_list['class'].extend([self.get_class_index(class_)]*len(self.dataset[class_][person]['rgb']))
                filtered_list['len'] += len(self.dataset[class_][person]['rgb'])
        if randomize:
            random.seed(self.random_seed)
            zipped = list(zip(filtered_list['rgb'],filtered_list['pose'],filtered_list['class']))
            random.shuffle(zipped)
            filtered_list['rgb'],filtered_list['pose'],filtered_list['class'] = zip(*zipped)
        return filtered_list

    def get_class_index(self,class_):
        return self.classes.index(class_)
    def get_class_name(self,index):
        return self.classes[index]
    def get_classes(self):
        return self.classes
    def get_persons(self):
        return self.persons
    def get_generator(self,filtered_list=None,mode = None,randomize=True,spatial_augument = None,fintuning = None):
        if filtered_list is None:
            filtered_list = self.filter(randomize=randomize)
        return Generator(filtered_list,
                         self.n_frames,
                         self.batch_size,
                         self.classes,
                         mode = mode,
                         cache_folder=self.cache_folder,
                         spatial_augument = spatial_augument)
        
class Generator(torch.utils.data.IterableDataset ):
    def __init__(self,
                 data_paths,
                 n_frames,
                 batch_size,
                 classes,
                 mode,
                 cache_folder,
                 num_join = 66,
                 spatial_augument = None) -> None:
        super(Generator).__init__()
        self.data_paths = data_paths
        self.n_frames = n_frames
        self.batch_size = batch_size
        self.mode = mode
        self.start = 0
        self.classes = classes
        self.end = len(data_paths['class'])
        self.cache_folder = cache_folder
        self.temperal_augument  = TemperalAugument(self.n_frames,mode=mode)
        self.spatial_transform = SpatialTransform(augument=spatial_augument)
        self.num_join = num_join
    def __len__(self):
        return self.end
    def __iter__(self):
         worker_info = torch.utils.data.get_worker_info()
         if worker_info is None:  # single-process data loading, return the full iterator
             iter_start = self.start
             iter_end = self.end
         else:  # in a worker process
             # split workload
             per_worker = int(math.ceil((self.end - self.start) / float(worker_info.num_workers)))
             worker_id = worker_info.id
             iter_start = self.start + worker_id * per_worker
             iter_end = min(iter_start + per_worker, self.end)
         return iter(self.get_data(iter_start, iter_end))
    

    def get_data(self,start,end):
        #create a list of labels
        labels = self.data_paths['class']
        batch = self.data_paths['pose']
        
        for i in range(start,end):
            path = batch[i]
            y = labels[i]
            X = np.load(path)[:,:self.num_join//2,:-1].reshape(-1,33*2)
            X_time = torch.tensor(self.temperal_augument.get_augmented_data(X)).float()
            X_spatial = X_time.permute(1,0)
            y = torch.nn.functional.one_hot(torch.tensor(y,dtype= torch.int64),len(self.classes)).float()
            yield  X_time,X_spatial, y

