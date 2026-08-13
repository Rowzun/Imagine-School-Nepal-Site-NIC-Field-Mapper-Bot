function scanMask = scanningDomain(shape, param, ...
                                   physMask, xC, yC, zC)
% SCANNINGDOMAIN  Build a logical mask for an inspection / scan volume
%                 that must lie inside an existing physical domain.
%
%   scanMask = SCANNINGDOMAIN(shape, param, physMask, xC, yC, zC)
%
%   Inputs
%   ------
%   shape    : 'block' | 'sphere' | 'cylinder'
%
%   param    : struct with fields that depend on shape
%              • 'block'    : P1, P2  (1×3 vectors, opposite corners)
%              • 'sphere'   : center  (1×3),   radius
%              • 'cylinder' : baseCenter (1×3), radius, height, normal (1×3)
%
%   physMask : logical 3-D array from PHYSICALDOMAIN (ny × nx × nz)
%   xC,yC,zC : vectors of voxel-centre coordinates (same sizes used to
%              produce physMask)
%
%   Output
%   -------
%   scanMask : logical 3-D array the same size as physMask.  TRUE where the
%              voxel centre lies inside the requested scanning volume.
%
%   The function throws an error if ANY voxel that belongs to scanMask lies
%   outside physMask (i.e. the scanning volume is not fully contained).
%
%   ----------------------------------------------------------------------

    %----------------------------------------------------------------------
    % Build centre-coordinate grids (ndgrid layout matches physMask: Y,X,Z)
    [X, Y, Z] = meshgrid(xC, yC, zC);

    switch lower(shape)
        case 'block'
            % param.P1, param.P2 : opposite corners
            p1 = param.P1(:).';   p2 = param.P2(:).';
            lo = min(p1, p2);     hi = max(p1, p2);

            scanMask =  X >= lo(1) & X <= hi(1) & ...
                        Y >= lo(2) & Y <= hi(2) & ...
                        Z >= lo(3) & Z <= hi(3);

        case 'sphere'
            % param.center, param.radius
            c = param.center(:).';   r = param.radius;
            scanMask = (X-c(1)).^2 + (Y-c(2)).^2 + (Z-c(3)).^2 <= r^2;

        case 'cylinder'
            % param.baseCenter, radius, height, normal
            cb = param.baseCenter(:);                 % column
            r  = param.radius;
            h  = param.height;
            u  = param.normal(:);   u = u / norm(u);  % unit axis

            % vector from base centre to each voxel centre
            PX = X - cb(1);   PY = Y - cb(2);   PZ = Z - cb(3);

            % axial coordinate t  (projection length along u)
            t = PX*u(1) + PY*u(2) + PZ*u(3);    % scalar projection

            % squared radial distance from axis
            d2 = (PX - t*u(1)).^2 + ...
                 (PY - t*u(2)).^2 + ...
                 (PZ - t*u(3)).^2;

            scanMask = (t >= 0) & (t <= h) & (d2 <= r^2);

        otherwise
            error('Unknown scanning shape "%s".',shape);
    end

    %----------------------------------------------------------------------
    % Containment test
    if any( scanMask(:) & ~physMask(:) )
        error('Requested scanning domain does not fit entirely inside the physical domain.');
    end
end
