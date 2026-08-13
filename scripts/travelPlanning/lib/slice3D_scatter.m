%%--- 3-slice colour-intensity map from scattered 3-D data --------------%%
%  INPUT  : pts  (N×4)  -> columns = [x  y  z  magnitude]
%           nGrid       -> # grid points per axis (scalar, optional)
%  OUTPUT : Figure with XY, XZ, YZ colour slices through (0,0,0)
% ----------------------------------------------------------------------- %

%function slice3D_scatter(pts,nGrid)
pts = datameasured;
% -------- user-adjustable defaults ------------------------------------ %
%if nargin<2,  nGrid = 101; end          % grid resolution
nGrid = 101;
markerSize  = 20;                        % size for over-plotted raw points
interpMode  = 'natural';                 % scatteredInterpolant method
fillValue   = NaN;                       % what to put outside the domain
colMap      = turbo;                     % colour map (MATLAB R2020b+)
% ---------------------------------------------------------------------- %

% --- split columns ----------------------------------------------------- %
x = pts(:,1);   y = pts(:,2);   z = pts(:,3);   v = pts(:,4);

% --- build a regular Cartesian grid covering the point cloud ---------- %
xmin = min(x);  xmax = max(x);
ymin = min(y);  ymax = max(y);
zmin = min(z);  zmax = max(z);

[xg,yg,zg] = ndgrid( ...
    linspace(xmin,xmax,nGrid), ...
    linspace(ymin,ymax,nGrid), ...
    linspace(zmin,zmax,nGrid));

% --- interpolate ------------------------------------------------------- %
F  = scatteredInterpolant(x,y,z,v,interpMode,'none');   % 'none' = fillValue
Vg = F(xg,yg,zg);

% --- convex-hull mask: use Delaunay tetrahedra ------------------------ %
DT  = delaunayTriangulation(x,y,z);                 % all tetrahedra
in  = ~isnan(DT.pointLocation([xg(:),yg(:),zg(:)]));% inside ↔ located
Vg(~in) = fillValue; 

% convert NDGRID → MESHGRID layout for slice()
X = permute(xg,[2 1 3]);
Y = permute(yg,[2 1 3]);
Z = permute(zg,[2 1 3]);
V = permute(Vg,[2 1 3]);

VdB = 20*log10(abs(V)./abs(max(max(max(V)))));

% --- define slice planes through the origin --------------------------- %
xs = 0;   ys = 0;   zs = 0;                       % (0,0,0) centre
figure('Color','w','Renderer','opengl'); hold on;

hs1 = slice(X,Y,Z,V,[],[],zs);
hs2 = slice(X,Y,Z,V,[],ys,[]);
hs3 = slice(X,Y,Z,V,xs,[],[]);


% --- tidy up the slices ---------------------------------------------- %
set([hs1,hs2,hs3],'EdgeColor','none','FaceAlpha',1);
colormap(colMap);  colorbar;
view(3);  axis equal tight vis3d;  box on;
xlabel('X'); ylabel('Y'); zlabel('Z');
title('Interpolated magnitude slices through (0,0,0)');


%end

