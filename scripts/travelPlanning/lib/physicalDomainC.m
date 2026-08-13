function [mask, xC, yC, zC, dx] = physicalDomainC(r, h, step, center)
% PHYSICALDOMAINC  Voxel mask for a cylinder centred at (cx,cy,cz).
%
%   [mask,xC,yC,zC,dx] = physicalDomainC(r,h,step)          % centre = [0 0 0]
%   [mask,xC,yC,zC,dx] = physicalDomainC(r,h,step,center)
%
%   The cylinder axis is the +Z direction.  Z runs from cz-h/2 to cz+h/2.

    arguments
        r      (1,1) double {mustBePositive}
        h      (1,1) double {mustBePositive}
        step   (1,1) double {mustBePositive}
        center (1,3) double = [0 0 0]
    end
    cx = center(1);  cy = center(2);  cz = center(3);

    % ---- lattice dimensions (integer voxels along each edge) ------------
    nx  = max(1, round(2*r / step));  dx = (2*r)/nx;
    ny  = nx;                         dy = dx;
    nz  = max(1, round(h   / step));  dz = h   /nz;

    % ---- voxel-centre coordinates ---------------------------------------
    xC = linspace(cx - r + dx/2, cx + r - dx/2, nx);
    yC = linspace(cy - r + dy/2, cy + r - dy/2, ny);
    zC = linspace(cz - h/2 + dz/2, cz + h/2 - dz/2, nz);

    [Xc,Yc,Zc] = meshgrid(xC,yC,zC);          % ny × nx × nz
    mask = (Xc-cx).^2 + (Yc-cy).^2 <= r^2;
end
