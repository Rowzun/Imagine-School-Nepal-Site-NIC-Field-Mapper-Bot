function h = drawVoxels(mask, xC, yC, zC, opts)
% DRAWBOXELS  Plot every TRUE voxel in a logical volume as a translucent cube
%
%   h = DRAWVOXELS(MASK, xC, yC, zC) takes
%       MASK   – logical 3-D array from physicalDomain (ny × nx × nz)
%       xC,yC,zC – vectors of voxel-centre coordinates along X,Y,Z
%
%   and draws one transparent cube per TRUE voxel.  The function returns the
%   Patch handle(s) created.
%
%   h = DRAWBOXELS(..., OPTS)  where OPTS is a struct of optional fields:
%       • Axes        → handle to plot into   (default: new figure/axes)
%       • Color       → RGB face colour       (default: [1 0 0]  = red)
%       • Alpha       → face transparency 0-1 (default: 0.2)
%       • EdgeColor   → edge colour or 'none' (default: 'none')
%
%   Example
%   -------
%     [M,xC,yC,zC] = physicalDomain(1.2,4,0.3);
%     cylinder3d(1.2,4,[1.2 1.2 0],[0 0 1]);  hold on          % shell
%     drawBoxels(M,xC,yC,zC);                                     % voxels
%

    %--------- defaults & input parsing -----------------------------------
    if nargin < 5, opts = struct; end
    if ~isfield(opts,'Axes')      || isempty(opts.Axes),      opts.Axes      = [];          end
    if ~isfield(opts,'Color')     || isempty(opts.Color),     opts.Color     = [1 0 0];    end
    if ~isfield(opts,'Alpha')     || isempty(opts.Alpha),     opts.Alpha     = 0.2;        end
    if ~isfield(opts,'EdgeColor') || isempty(opts.EdgeColor), opts.EdgeColor = 'none';     end
    if ~isfield(opts,'LineStyle'), opts.LineStyle = '-'; end

    if isempty(opts.Axes)
        fig = figure('Color','w');
        ax  = axes(fig);  axis(ax,'equal');  grid(ax,'on');
        view(ax,3);
    else
        ax = opts.Axes;
        hold(ax,'on');
    end

    %--------- half-widths of a voxel -------------------------------------
    dx2 = (numel(xC)>1) * (xC(2)-xC(1))/2 + (numel(xC)==1)*0.5;
    dy2 = dx2;                                   % square cross-section
    dz2 = (numel(zC)>1) * (zC(2)-zC(1))/2 + (numel(zC)==1)*0.5;

    %--------- coordinates of voxel centres that are TRUE -----------------
    [iY,iX,iZ] = ind2sub(size(mask), find(mask));
    xc = xC(iX).';   yc = yC(iY).';   zc = zC(iZ).';

    %--------- build one big vertices/faces list (faster than per-cube) ----
    nVox   = numel(xc);
    V      = zeros(8*nVox,3);          % 8 vertices per voxel
    F      = zeros(6*nVox,4);          % 6 faces  per voxel
    for k = 1:nVox
        baseV = 8*(k-1);
        baseF = 6*(k-1);

        % vertices (x y z) for voxel k
        x0 = xc(k)-dx2;  x1 = xc(k)+dx2;
        y0 = yc(k)-dy2;  y1 = yc(k)+dy2;
        z0 = zc(k)-dz2;  z1 = zc(k)+dz2;
        V(baseV+(1:8),:) = [ x0 y0 z0;
                             x1 y0 z0;
                             x1 y1 z0;
                             x0 y1 z0;
                             x0 y0 z1;
                             x1 y0 z1;
                             x1 y1 z1;
                             x0 y1 z1 ];

        % faces (indices into V) for voxel k
        idx = baseV + (1:8);
        F(baseF+(1:6),:) = [ idx([1 2 3 4]);   % bottom
                             idx([5 6 7 8]);   % top
                             idx([1 2 6 5]);   % sides…
                             idx([2 3 7 6]);
                             idx([3 4 8 7]);
                             idx([4 1 5 8]) ];
    end

    %--------- draw all cubes at once -------------------------------------
    h = patch('Parent',ax, 'Faces',F, 'Vertices',V, ...
              'FaceColor',opts.Color, ...
              'EdgeColor',opts.EdgeColor, ...
              'LineStyle',opts.LineStyle,...
              'FaceAlpha',opts.Alpha);

    if isempty(opts.Axes), xlabel(ax,'X'); ylabel(ax,'Y'); zlabel(ax,'Z'); end
end
