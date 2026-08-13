%% Main Camera — test sphere
% (assumes physicalDomain, scanningDomain, scanTrajectory, cylinder3d,
%  animateTrajectory, and drawBoxels are already on the MATLAB path)

% ------------------------------------------------------------------------
%the inner bore diameter is 100mm
%the length is 254 mm
addpath('lib')

% 1) MRI bore
r     = 50;        % cylinder radius  [mm]
h     = 254;        % cylinder height  [mm]
ctr   = [0 0 0];     % Adjust for the Bore [mm]

step  = 5;        % voxel size       [mm]
waitT = 0.005;        % pause between frames [s]
% For visualization
az    = 30;         % camera azimuth
el    = 30;         % camera elevation

% ------------------------------------------------------------------------
% 2) BUILD DOMAINS
% This domaind depends on the scanner
%[physMask,xC,yC,zC] = physicalDomain(r,h,step,ctr);
[physMask,xC,yC,zC] = physicalDomainC(r,h,step,ctr);


% ----- choose any scan volume: here a centred sphere --------------------

paramSphere.center = [ctr(1) ctr(2) ctr(3)];
paramSphere.radius = 45;
scanMask = scanningDomain('sphere',paramSphere,...
                          physMask,xC,yC,zC);
%  alternatives : 'block' | 'sphere' | 'cylinder'

% ------------------------------------------------------------------------
% 3) GENERATE TRAJECTORY (pick your algorithm)
path = scanTrajectory(scanMask,xC,yC,zC,'layerwise');
%   alternatives: 'boustrophedon' 'greedy'  'tsp'  'layerwise'
%tsp requires pdist2 within Statistics and Machine Learning Toolbox.
% ------------------------------------------------------------------------
%%
% 4) DRAW ULTRA-TRANSPARENT CYLINDER SHELL
%ax = cylinder3d(r, h, ctr, [0 0 1], 40, 0.05);  % faint shell
ax = cylinder3dC(r,h,ctr, [0 0 1], 40, 0.05);   hold(ax,'on');

hold(ax,'on');

% --------------------------------------------------------------------
% Force a white canvas for the GIF
fig = ax.Parent;          % the figure that cylinder3d just created/returned
set(fig,'Color','w');     % white figure background
set(ax, 'Color','w');     % white axes background  (use 'none' for transparent)
% --------------------------------------------------------------------

% ------------------------------------------------------------------------
% 5) FREEZE AXES SO NOTHING RESCALES DURING ANIMATION
%axis(ax,'equal');
% camera orientation
view(ax,az,el);                   % az = 30°, el = 30°
axis(ax,[ctr(1)-r ctr(1)+r  ctr(2)-r ctr(2)+r  -h/2 h/2]);     % lock X, Y, Z limits
axis(ax,'vis3d','manual');        % no automatic scale negotiation



% ------------------------------------------------------------------------
% 6) RUN THE STEP-BY-STEP ANIMATION
%animateTrajectory(scanMask,xC,yC,zC,path,waitT,ax);                 % on-screen only
%animateTrajectory(scanMask,xC,yC,zC,path,waitT,ax,'traj_anim_sphere_boust.gif'); % + save GIF



% ------------------------------------------------------------------------
% 7) SAVIND DATA
%savePath(path,'trajectory_sphere_boust.csv','csv');   %           → CSV
%savePath(path,'trajectory_sphere_boust.txt','ascii'); % second copy→ space-delimited

% ------------------------------------------------------------------------
% 8) EVALUATING DISTANCE

d = travelDistance(path)/1000;%[m]
disp(d)